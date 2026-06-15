import 'package:equatable/equatable.dart';

abstract class EnrollState extends Equatable {
  @override
  List<Object?> get props => [];
}

class EnrollInitial extends EnrollState {}

class EnrollLoading extends EnrollState {}

class EnrollStatusLoaded extends EnrollState {
  final int samplesReceived;
  final int samplesRequired;
  final bool isEnrolled;

  EnrollStatusLoaded({
    required this.samplesReceived,
    required this.samplesRequired,
    required this.isEnrolled,
  });

  @override
  List<Object?> get props => [samplesReceived, samplesRequired, isEnrolled];
}

class EnrollRecording extends EnrollState {}

class EnrollSuccess extends EnrollState {
  final String message;
  final int samplesReceived;
  final bool isEnrolled;

  EnrollSuccess({
    required this.message,
    required this.samplesReceived,
    required this.isEnrolled,
  });

  @override
  List<Object?> get props => [message, samplesReceived, isEnrolled];
}

class EnrollError extends EnrollState {
  final String message;

  EnrollError({required this.message});

  @override
  List<Object?> get props => [message];
}