import 'package:equatable/equatable.dart';

abstract class VoicePayEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class StartRecording extends VoicePayEvent {}

class StopRecording extends VoicePayEvent {}

class PaymentParsed extends VoicePayEvent {
  final String? customAmount;
  final String? customUpiId;

  PaymentParsed({this.customAmount, this.customUpiId});

  @override
  List<Object?> get props => [customAmount, customUpiId];
}

class ConfirmPayment extends VoicePayEvent {}

class CancelPayment extends VoicePayEvent {}

class ResetPayment extends VoicePayEvent {}
