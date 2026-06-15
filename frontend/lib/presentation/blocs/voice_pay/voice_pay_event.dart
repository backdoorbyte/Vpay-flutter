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

class SubmitVoiceConfirmation extends VoicePayEvent {
  final String audioPath;

  SubmitVoiceConfirmation(this.audioPath);

  @override
  List<Object?> get props => [audioPath];
}

class CancelPayment extends VoicePayEvent {}

class SetLanguage extends VoicePayEvent {
  final String language;

  SetLanguage(this.language);

  @override
  List<Object?> get props => [language];
}

class ResetPayment extends VoicePayEvent {}

class SetQrData extends VoicePayEvent {
  final String? upiId;
  final double? amount;
  final String? note;

  SetQrData({this.upiId, this.amount, this.note});

  @override
  List<Object?> get props => [upiId, amount, note];
}

class AutoCreateIntent extends VoicePayEvent {
  final String upiId;
  final double amount;
  final String? note;

  AutoCreateIntent({required this.upiId, required this.amount, this.note});

  @override
  List<Object?> get props => [upiId, amount, note];
}
