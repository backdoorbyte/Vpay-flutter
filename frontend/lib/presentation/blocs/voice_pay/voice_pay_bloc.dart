import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/utils/audio_recorder.dart';
import '../../../data/models/payment_intent.dart';
import '../../../data/repositories/voice_pay_repository.dart';
import 'voice_pay_event.dart';
import 'voice_pay_state.dart';

class VoicePayBloc extends Bloc<VoicePayEvent, VoicePayState> {
  final VoicePayRepository _voicePayRepository;
  final AudioRecorderService _audioRecorder;

  PaymentIntentResponse? _lastIntent;
  bool _isAutoConfirm = false;

  // QR flow state
  String? _presetUpiId;
  String? _presetNote;
  bool _isWaitingForAmount = false;

  VoicePayBloc({
    VoicePayRepository? voicePayRepository,
    AudioRecorderService? audioRecorder,
  })  : _voicePayRepository = voicePayRepository ?? VoicePayRepository(),
        _audioRecorder = audioRecorder ?? AudioRecorderService(),
        super(VoicePayInitial()) {
    on<StartRecording>(_onStartRecording);
    on<StopRecording>(_onStopRecording);
    on<SubmitVoiceConfirmation>(_onSubmitVoiceConfirmation);
    on<SetLanguage>(_onSetLanguage);
    on<CancelPayment>(_onCancelPayment);
    on<ResetPayment>(_onResetPayment);
    on<SetQrData>(_onSetQrData);
    on<AutoCreateIntent>(_onAutoCreateIntent);
  }

  Future<void> _onStartRecording(StartRecording event, Emitter<VoicePayState> emit) async {
    await _audioRecorder.startRecording();
    if (_isAutoConfirm) {
      emit(VoicePayListening());
    } else {
      emit(VoicePayRecording());
    }
  }

  Future<void> _onStopRecording(StopRecording event, Emitter<VoicePayState> emit) async {
    try {
      final path = await _audioRecorder.stopRecording();

      if (_isAutoConfirm && path != null) {
        // Voice confirmation flow
        emit(VoicePayVerifying());
        try {
          if (_lastIntent != null) {
            final result = await _voicePayRepository.confirmPayment(
              _lastIntent!.intentId,
              path,
            );
            if (result.verified && result.paymentCompleted) {
              emit(VoicePaySuccess(result: result));
            } else {
              emit(VoicePayError(
                message: result.message,
              ));
            }
          } else {
            emit(VoicePayError(message: 'No payment intent found'));
          }
        } catch (e) {
          emit(VoicePayError(message: e.toString()));
        }
        _isAutoConfirm = false;
      } else if (!_isAutoConfirm && path != null) {
        // Check if we are waiting for amount from QR flow
        if (_isWaitingForAmount && _presetUpiId != null) {
          await _handleAmountOnlyParse(path, emit);
        } else {
          await _handleFullParse(path, emit);
        }
      }
    } catch (e) {
      emit(VoicePayError(message: e.toString()));
    }
  }

  Future<void> _handleFullParse(String path, Emitter<VoicePayState> emit) async {
    // Initial payment parsing flow
    emit(VoicePayProcessing());
    try {
      final response = await _voicePayRepository.voicePayParse(path, language: null);

      if (response.parsed.amount != null && response.parsed.upiId != null) {
        // Create payment intent
        final intentReq = PaymentIntentRequest(
          recipient: response.parsed.recipient ?? response.parsed.upiId ?? '',
          upiId: response.parsed.upiId!,
          amount: response.parsed.amount!,
          note: response.parsed.note,
          language: response.language,
        );
        final intent = await _voicePayRepository.createPaymentIntent(intentReq);
        _lastIntent = intent;

        // Enable auto-confirm mode for next recording
        _isAutoConfirm = true;

        emit(VoicePayConfirm(
          parsed: response,
          intent: intent,
          displayText: intent.displayText,
          confirmPrompt: intent.confirmPrompt,
          language: response.language,
        ));
      } else {
        // Provide specific error message
        String errorMessage = 'Could not parse payment details. Please try again.';
        if (response.parsed.amount != null && response.parsed.upiId == null) {
          if (response.parsed.recipient != null) {
            errorMessage = 'Contact "${response.parsed.recipient}" not found in your contacts. Please save the contact first or say the UPI ID directly.';
          } else {
            errorMessage = 'Amount recognized, but no recipient found. Please say the recipient name or UPI ID.';
          }
        } else if (response.parsed.amount == null && response.parsed.recipient != null) {
          errorMessage = 'Recipient "${response.parsed.recipient}" found, but could not understand the amount. Please say the amount clearly (e.g., "500 rupaye").';
        }
        emit(VoicePayError(message: errorMessage));
      }
    } catch (e) {
      emit(VoicePayError(message: e.toString()));
    }
  }

  Future<void> _handleAmountOnlyParse(String path, Emitter<VoicePayState> emit) async {
    // QR flow: parse only the amount from the audio
    emit(VoicePayProcessing());
    try {
      final response = await _voicePayRepository.voicePayParse(path, language: null);

      if (response.parsed.amount != null && _presetUpiId != null) {
        final intentReq = PaymentIntentRequest(
          recipient: _presetUpiId!,
          upiId: _presetUpiId!,
          amount: response.parsed.amount!,
          note: _presetNote ?? response.parsed.note,
          language: response.language,
        );
        final intent = await _voicePayRepository.createPaymentIntent(intentReq);
        _lastIntent = intent;
        _isAutoConfirm = true;
        _isWaitingForAmount = false;

        emit(VoicePayConfirm(
          parsed: response,
          intent: intent,
          displayText: intent.displayText,
          confirmPrompt: intent.confirmPrompt,
          language: response.language,
        ));
      } else {
        _isWaitingForAmount = true;
        emit(VoicePayError(message: 'Could not understand the amount. Please try again.'));
      }
    } catch (e) {
      _isWaitingForAmount = true;
      emit(VoicePayError(message: e.toString()));
    }
  }

  Future<void> _onSubmitVoiceConfirmation(
    SubmitVoiceConfirmation event,
    Emitter<VoicePayState> emit,
  ) async {
    emit(VoicePayVerifying());
    try {
      if (_lastIntent != null) {
        final result = await _voicePayRepository.confirmPayment(
          _lastIntent!.intentId,
          event.audioPath,
        );
        if (result.verified && result.paymentCompleted) {
          emit(VoicePaySuccess(result: result));
        } else {
          emit(VoicePayError(message: result.message));
        }
      } else {
        emit(VoicePayError(message: 'No payment intent found'));
      }
    } catch (e) {
      emit(VoicePayError(message: e.toString()));
    }
  }

  void _onSetLanguage(SetLanguage event, Emitter<VoicePayState> emit) {
    // Language is now auto-detected; this is kept for compatibility
  }

  void _onSetQrData(SetQrData event, Emitter<VoicePayState> emit) {
    _presetUpiId = event.upiId;
    _presetNote = event.note;

    final upiId = event.upiId;
    final amount = event.amount;
    if (upiId != null && amount != null) {
      // QR has both UPI and amount -> auto-create intent
      add(AutoCreateIntent(upiId: upiId, amount: amount, note: event.note));
    } else if (upiId != null) {
      // QR has UPI but no amount -> ask for amount
      _isWaitingForAmount = true;
      emit(VoicePayNeedsAmount(upiId: upiId, note: event.note));
    }
  }

  Future<void> _onAutoCreateIntent(AutoCreateIntent event, Emitter<VoicePayState> emit) async {
    try {
      final intentReq = PaymentIntentRequest(
        recipient: event.upiId,
        upiId: event.upiId,
        amount: event.amount,
        note: event.note,
      );
      final intent = await _voicePayRepository.createPaymentIntent(intentReq);
      _lastIntent = intent;
      _isAutoConfirm = true;
      _isWaitingForAmount = false;

      emit(VoicePayConfirm(
        parsed: null,
        intent: intent,
        displayText: intent.displayText,
        confirmPrompt: intent.confirmPrompt,
        language: 'en',
      ));
    } catch (e) {
      emit(VoicePayError(message: e.toString()));
    }
  }

  void _onCancelPayment(CancelPayment event, Emitter<VoicePayState> emit) {
    _isAutoConfirm = false;
    _isWaitingForAmount = false;
    emit(VoicePayInitial());
  }

  void _onResetPayment(ResetPayment event, Emitter<VoicePayState> emit) {
    _lastIntent = null;
    _isAutoConfirm = false;
    _isWaitingForAmount = false;
    _presetUpiId = null;
    _presetNote = null;
    emit(VoicePayInitial());
  }

  @override
  Future<void> close() {
    _audioRecorder.dispose();
    return super.close();
  }
}
