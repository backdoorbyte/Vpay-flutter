import 'package:dio/dio.dart';

import '../../core/constants/api_constants.dart';
import '../../core/network/api_client.dart';
import '../models/enroll_response.dart';
import '../models/verify_response.dart';

class EnrollRepository {
  final ApiClient _apiClient;

  EnrollRepository({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  Future<EnrollResponse> submitEnrollSample(String audioFilePath, {String mode = 'single'}) async {
    final formData = FormData.fromMap({
      'audio': await MultipartFile.fromFile(audioFilePath),
      'mode': mode,
    });
    final response = await _apiClient.post(ApiConstants.enroll, data: formData);
    return EnrollResponse.fromJson(response.data as Map<String, dynamic>);
  }

  Future<EnrollStatusResponse> getEnrollStatus() async {
    final response = await _apiClient.get(ApiConstants.enrollStatus);
    return EnrollStatusResponse.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> resetEnrollment() async {
    await _apiClient.delete(ApiConstants.enrollReset);
  }

  Future<VerifyResponse> verifySpeaker(String audioFilePath) async {
    final formData = FormData.fromMap({
      'audio': await MultipartFile.fromFile(audioFilePath),
    });
    final response = await _apiClient.post(ApiConstants.verify, data: formData);
    return VerifyResponse.fromJson(response.data as Map<String, dynamic>);
  }
}
