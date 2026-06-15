import 'package:equatable/equatable.dart';

abstract class FaceEnrollEvent extends Equatable {
  const FaceEnrollEvent();

  @override
  List<Object?> get props => [];
}

class FaceEnrollInitialize extends FaceEnrollEvent {}

class FaceEnrollCapture extends FaceEnrollEvent {}

class FaceEnrollCheckStatus extends FaceEnrollEvent {}

class FaceEnrollReset extends FaceEnrollEvent {}