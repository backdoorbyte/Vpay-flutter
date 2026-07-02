import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/services/face_verification_service.dart';
import '../../../data/repositories/face_repository.dart';
import 'face_enroll_event.dart';
import 'face_enroll_state.dart';

class FaceEnrollBloc extends Bloc<FaceEnrollEvent, FaceEnrollState> {
  final FaceRepository _faceRepository;
  final FaceVerificationService _faceVerificationService;

  FaceEnrollBloc(this._faceRepository, this._faceVerificationService) : super(FaceEnrollInitial()) {
    on<FaceEnrollInitialize>(_onInitialize);
    on<FaceEnrollCapture>(_onCapture);
    on<FaceEnrollCheckStatus>(_onCheckStatus);
    on<FaceEnrollReset>(_onReset);
  }

  Future<void> _onInitialize(
    FaceEnrollInitialize event,
    Emitter<FaceEnrollState> emit,
  ) async {
    await _checkStatus(emit);
  }

  Future<void> _onCapture(
    FaceEnrollCapture event,
    Emitter<FaceEnrollState> emit,
  ) async {
    emit(FaceEnrollLoading());

    // Yield to main thread to allow UI to render loading state before heavy capture
    await Future.delayed(const Duration(milliseconds: 50));

    try {
      final success = await _faceVerificationService.enrollFace(userId: 1);
      if (success) {
        emit(const FaceEnrollSuccess(message: 'Face enrolled successfully'));
        await _checkStatus(emit);
      } else {
        emit(const FaceEnrollError(message: 'Failed to enroll face'));
      }
    } catch (e) {
      emit(FaceEnrollError(message: 'Enrollment failed: $e'));
    }
  }

  Future<void> _onCheckStatus(
    FaceEnrollCheckStatus event,
    Emitter<FaceEnrollState> emit,
  ) async {
    await _checkStatus(emit);
  }

  Future<void> _checkStatus(Emitter<FaceEnrollState> emit) async {
    try {
      final isEnrolled = await _faceRepository.checkFaceEnrollmentStatus(userId: 1);
      emit(FaceEnrollStatusLoaded(isFaceEnrolled: isEnrolled));
    } catch (e) {
      emit(FaceEnrollError(message: 'Status check failed: $e'));
    }
  }

  Future<void> _onReset(
    FaceEnrollReset event,
    Emitter<FaceEnrollState> emit,
  ) async {
    emit(FaceEnrollLoading());
    try {
      final success = await _faceRepository.resetFaceEnrollment(userId: 1);
      if (success) {
        emit(const FaceEnrollResetSuccess(message: 'Face enrollment reset'));
        await _checkStatus(emit);
      } else {
        emit(const FaceEnrollError(message: 'Failed to reset face enrollment'));
      }
    } catch (e) {
      emit(FaceEnrollError(message: 'Reset failed: $e'));
    }
  }
}