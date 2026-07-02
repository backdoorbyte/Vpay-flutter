import 'dart:io';

import 'package:dio/dio.dart';

import '../../core/constants/api_constants.dart';
import '../../core/network/api_client.dart';
import '../models/confirm_response.dart';
import '../models/payment_intent.dart';
import '../models/voice_pay_response.dart';
import 'face_repository.dart';

class VoicePayRepository {
  final ApiClient _apiClient;
  late final FaceRepository _faceRepository;

  VoicePayRepository({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient() {
    _faceRepository = FaceRepository(apiClient: _apiClient);
  }

  /// Get the face repository for face verification operations
  FaceRepository get face => _faceRepository;

  Future<VoicePayResponse> voicePayParse(String audioFilePath, {String? language}) async {
    final fileSize = await File(audioFilePath).length();
    assert(fileSize > 0, 'WAV file is empty: $audioFilePath');
    print('[VoicePayRepo] Sending audio file: $audioFilePath ($fileSize bytes)');
    String url = ApiConstants.voicePayParse;
    if (language != null && language.isNotEmpty) {
      url = '$url?language=$language';
    }
    final formData = FormData.fromMap({
      'audio': await MultipartFile.fromFile(audioFilePath),
    });
    final response = await _apiClient.post(url, data: formData);
    return VoicePayResponse.fromJson(response.data as Map<String, dynamic>);
  }

  Future<PaymentIntentResponse> createPaymentIntent(PaymentIntentRequest request) async {
    final response = await _apiClient.post(ApiConstants.paymentIntent, data: request.toJson());
    return PaymentIntentResponse.fromJson(response.data as Map<String, dynamic>);
  }

  Future<ConfirmVerifyResponse> confirmPayment(int intentId, String audioFilePath) async {
    final fileSize = await File(audioFilePath).length();
    assert(fileSize > 0, 'WAV file is empty: $audioFilePath');
    print('[VoicePayRepo] Sending audio file: $audioFilePath ($fileSize bytes)');
    final formData = FormData.fromMap({
      'audio': await MultipartFile.fromFile(audioFilePath),
    });
    final response = await _apiClient.post(
      '${ApiConstants.voicePayConfirm}?intent_id=$intentId',
      data: formData,
    );
    return ConfirmVerifyResponse.fromJson(response.data as Map<String, dynamic>);
  }
}
