import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../data/repositories/enroll_repository.dart';
import 'enroll_event.dart';
import 'enroll_state.dart';

class EnrollBloc extends Bloc<EnrollEvent, EnrollState> {
  final EnrollRepository _enrollRepository;

  EnrollBloc({EnrollRepository? enrollRepository})
      : _enrollRepository = enrollRepository ?? EnrollRepository(),
        super(EnrollInitial()) {
    on<CheckEnrollStatus>(_onCheckStatus);
    on<SubmitEnrollSample>(_onSubmitSample);
    on<ResetEnrollment>(_onReset);
    on<StartEnrollRecording>((event, emit) => emit(EnrollRecording()));
  }

  Future<void> _onCheckStatus(CheckEnrollStatus event, Emitter<EnrollState> emit) async {
    emit(EnrollLoading());
    try {
      final status = await _enrollRepository.getEnrollStatus();
      emit(EnrollStatusLoaded(
        samplesReceived: status.samplesReceived,
        samplesRequired: status.samplesRequired,
        isEnrolled: status.isVoiceEnrolled,
      ));
    } catch (e) {
      emit(EnrollError(message: e.toString()));
    }
  }

  Future<void> _onSubmitSample(SubmitEnrollSample event, Emitter<EnrollState> emit) async {
    emit(EnrollLoading());
    try {
      final result = await _enrollRepository.submitEnrollSample(event.audioPath);
      emit(EnrollSuccess(
        message: result.message,
        samplesReceived: result.samplesReceived,
        isEnrolled: result.enrolled,
      ));
      add(CheckEnrollStatus());
    } catch (e) {
      emit(EnrollError(message: e.toString()));
    }
  }

  Future<void> _onReset(ResetEnrollment event, Emitter<EnrollState> emit) async {
    emit(EnrollLoading());
    try {
      await _enrollRepository.resetEnrollment();
      add(CheckEnrollStatus());
    } catch (e) {
      emit(EnrollError(message: e.toString()));
    }
  }
}