import 'package:equatable/equatable.dart';

abstract class EnrollEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class CheckEnrollStatus extends EnrollEvent {}

class StartEnrollRecording extends EnrollEvent {}

class SubmitEnrollSample extends EnrollEvent {
  final String audioPath;

  SubmitEnrollSample(this.audioPath);

  @override
  List<Object?> get props => [audioPath];
}

class ResetEnrollment extends EnrollEvent {}