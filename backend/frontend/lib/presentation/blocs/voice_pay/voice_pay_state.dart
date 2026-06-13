import 'package:equatable/equatable.dart';

import '../../../data/models/confirm_response.dart';
import '../../../data/models/payment_intent.dart';
import '../../../data/models/voice_pay_response.dart';

abstract class VoicePayState extends Equatable {
  @override
  List<Object?> get props => [];
}

class VoicePayInitial extends VoicePayState {}

class VoicePayRecording extends VoicePayState {
  final bool isRecording;

  VoicePayRecording({this.isRecording = true});

  @override
  List<Object?> get props => [isRecording];
}

class VoicePayProcessing extends VoicePayState {}

class VoicePayConfirm extends VoicePayState {
  final VoicePayResponse? parsed;
  final PaymentIntentResponse? intent;
  final String displayText;
  final String confirmPrompt;

  VoicePayConfirm({
    this.parsed,
    this.intent,
    this.displayText = '',
    this.confirmPrompt = '',
  });

  @override
  List<Object?> get props => [parsed, intent, displayText, confirmPrompt];
}

class VoicePayListening extends VoicePayState {
  final String? transcript;

  VoicePayListening({this.transcript});

  @override
  List<Object?> get props => [transcript];
}

class VoicePayVerifying extends VoicePayState {}

class VoicePaySuccess extends VoicePayState {
  final ConfirmVerifyResponse result;

  VoicePaySuccess({required this.result});

  @override
  List<Object?> get props => [result];
}

class VoicePayError extends VoicePayState {
  final String message;

  VoicePayError({required this.message});

  @override
  List<Object?> get props => [message];
}
