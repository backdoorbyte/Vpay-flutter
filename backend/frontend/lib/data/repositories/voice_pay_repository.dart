import 'package:dio/dio.dart';

import '../../core/constants/api_constants.dart';
import '../../core/network/api_client.dart';
import '../models/confirm_response.dart';
import '../models/payment_intent.dart';
import '../models/voice_pay_response.dart';

class VoicePayRepository {
  final ApiClient _apiClient;

  VoicePayRepository({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  Future<VoicePayResponse> voicePayParse(String audioFilePath) async {
    final formData = FormData.fromMap({
      'audio': await MultipartFile.fromFile(audioFilePath),
    });
    final response = await _apiClient.post(ApiConstants.voicePayParse, data: formData);
    return VoicePayResponse.fromJson(response.data as Map<String, dynamic>);
  }

  Future<PaymentIntentResponse> createPaymentIntent(PaymentIntentRequest request) async {
    final response = await _apiClient.post(ApiConstants.paymentIntent, data: request.toJson());
    return PaymentIntentResponse.fromJson(response.data as Map<String, dynamic>);
  }

  Future<ConfirmVerifyResponse> confirmPayment(int intentId, String audioFilePath) async {
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
