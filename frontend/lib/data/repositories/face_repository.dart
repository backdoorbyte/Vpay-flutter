import 'package:dio/dio.dart';

import '../../core/constants/api_constants.dart';
import '../../core/network/api_client.dart';

/// Repository for face verification operations
class FaceRepository {
  final ApiClient _apiClient;

  FaceRepository({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  /// Enroll a face for the user
  Future<bool> enrollFace(String imagePath, {int userId = 1}) async {
    try {
      print('[FaceRepository] Enrolling face from: $imagePath');

      final formData = FormData.fromMap({
        'image': await MultipartFile.fromFile(
          imagePath,
          filename: 'face_$userId.jpg',
        ),
      });

      final response = await _apiClient.post(
        ApiConstants.faceEnroll,
        data: formData,
      );

      final data = response.data as Map<String, dynamic>;
      final success = data['success'] as bool? ?? false;
      final message = data['message'] as String? ?? 'Unknown error';

      print('[FaceRepository] Enrollment response: success=$success, message=$message');
      return success;
    } catch (e) {
      print('[FaceRepository] Enrollment failed: $e');
      return false;
    }
  }

  /// Verify a face against enrolled embedding
  Future<FaceVerificationResult> verifyFace(
    String imagePath, {
    int userId = 1,
    double threshold = 0.6,
  }) async {
    try {
      final formData = FormData.fromMap({
        'image': await MultipartFile.fromFile(
          imagePath,
          filename: 'verify_$userId.jpg',
        ),
      });

      final response = await _apiClient.post(
        '${ApiConstants.faceVerify}?threshold=$threshold',
        data: formData,
      );

      final data = response.data as Map<String, dynamic>;
      return FaceVerificationResult.fromJson(data);
    } catch (e) {
      print('[FaceRepository] Verification failed: $e');
      return FaceVerificationResult(
        verified: false,
        confidence: 0.0,
        message: 'Verification error: $e',
      );
    }
  }

  /// Check face enrollment status
  Future<bool> checkFaceEnrollmentStatus({int userId = 1}) async {
    try {
      final response = await _apiClient.get(ApiConstants.faceStatus);
      final data = response.data as Map<String, dynamic>;
      return data['is_face_enrolled'] as bool? ?? false;
    } catch (e) {
      print('[FaceRepository] Status check failed: $e');
      return false;
    }
  }

  /// Reset face enrollment
  Future<bool> resetFaceEnrollment({int userId = 1}) async {
    try {
      final response = await _apiClient.delete(ApiConstants.faceReset);
      final data = response.data as Map<String, dynamic>;
      return data['success'] as bool? ?? false;
    } catch (e) {
      print('[FaceRepository] Reset failed: $e');
      return false;
    }
  }
}

/// Face verification result model
class FaceVerificationResult {
  final bool verified;
  final double confidence;
  final String message;

  FaceVerificationResult({
    required this.verified,
    required this.confidence,
    required this.message,
  });

  factory FaceVerificationResult.fromJson(Map<String, dynamic> json) {
    return FaceVerificationResult(
      verified: json['verified'] as bool? ?? false,
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      message: json['message'] as String? ?? '',
    );
  }
}