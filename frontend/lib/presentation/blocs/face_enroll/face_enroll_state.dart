import 'package:equatable/equatable.dart';

abstract class FaceEnrollState extends Equatable {
  const FaceEnrollState();

  @override
  List<Object?> get props => [];
}

class FaceEnrollInitial extends FaceEnrollState {}

class FaceEnrollLoading extends FaceEnrollState {}

class FaceEnrollStatusLoaded extends FaceEnrollState {
  final bool isFaceEnrolled;

  const FaceEnrollStatusLoaded({required this.isFaceEnrolled});

  @override
  List<Object?> get props => [isFaceEnrolled];
}

class FaceEnrollSuccess extends FaceEnrollState {
  final String message;

  const FaceEnrollSuccess({required this.message});

  @override
  List<Object?> get props => [message];
}

class FaceEnrollError extends FaceEnrollState {
  final String message;

  const FaceEnrollError({required this.message});

  @override
  List<Object?> get props => [message];
}

class FaceEnrollResetSuccess extends FaceEnrollState {
  final String message;

  const FaceEnrollResetSuccess({required this.message});

  @override
  List<Object?> get props => [message];
}