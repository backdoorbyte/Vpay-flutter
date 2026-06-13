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

  VoicePayBloc({
    VoicePayRepository? voicePayRepository,
    AudioRecorderService? audioRecorder,
  })  : _voicePayRepository = voicePayRepository ?? VoicePayRepository(),
        _audioRecorder = audioRecorder ?? AudioRecorderService(),
        super(VoicePayInitial()) {
    on<StartRecording>(_onStartRecording);
    on<StopRecording>(_onStopRecording);
    on<CancelPayment>(_onCancelPayment);
    on<ResetPayment>(_onResetPayment);
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
        // Initial payment parsing flow
        emit(VoicePayProcessing());
        try {
          final response = await _voicePayRepository.voicePayParse(path);

          if (response.parsed.amount != null && response.parsed.upiId != null) {
            // Create payment intent
            final intentReq = PaymentIntentRequest(
              recipient: response.parsed.recipient ?? response.parsed.upiId ?? '',
              upiId: response.parsed.upiId!,
              amount: response.parsed.amount!,
              note: response.parsed.note,
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
            ));
          } else {
            emit(VoicePayError(message: 'Could not parse payment details. Please try again.'));
          }
        } catch (e) {
          emit(VoicePayError(message: e.toString()));
        }
      }
    } catch (e) {
      emit(VoicePayError(message: e.toString()));
    }
  }

  void _onCancelPayment(CancelPayment event, Emitter<VoicePayState> emit) {
    _isAutoConfirm = false;
    emit(VoicePayInitial());
  }

  void _onResetPayment(ResetPayment event, Emitter<VoicePayState> emit) {
    _lastIntent = null;
    _isAutoConfirm = false;
    emit(VoicePayInitial());
  }

  @override
  Future<void> close() {
    _audioRecorder.dispose();
    return super.close();
  }
}