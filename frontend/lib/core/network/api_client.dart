import 'dart:developer';

import 'package:dio/dio.dart';

import '../constants/api_constants.dart';

class ApiClient {
  late final Dio _dio;

  ApiClient() {
    _dio = Dio(
      BaseOptions(
        baseUrl: ApiConstants.baseUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 60),
        sendTimeout: const Duration(seconds: 60),
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      ),
    );

    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          log('[API Request] ${options.method} ${options.baseUrl}${options.path}');
          return handler.next(options);
        },
        onResponse: (response, handler) {
          log('[API Response] ${response.statusCode} - ${response.requestOptions.path}');
          return handler.next(response);
        },
        onError: (error, handler) {
          log('[API Error] ${error.type} - ${error.message}');
          log('[API Error Details] Path: ${error.requestOptions.path}, Attempted URL: ${error.requestOptions.baseUrl}${error.requestOptions.path}');
          return handler.next(error);
        },
      ),
    );
  }

  Dio get dio => _dio;

  // --- GET ---
  Future<Response> get(String path, {Map<String, dynamic>? queryParams}) async {
    return _dio.get(path, queryParameters: queryParams);
  }

  // --- POST ---
  Future<Response> post(String path, {dynamic data, Options? options}) async {
    return _dio.post(path, data: data, options: options);
  }

  // --- DELETE ---
  Future<Response> delete(String path) async {
    return _dio.delete(path);
  }

  // --- Multipart for audio ---
  Future<Response> postMultipart(
    String path, {
    required String field,
    required String filePath,
    String? mimeType,
    Map<String, dynamic>? extraFields,
  }) async {
    final formData = FormData.fromMap({
      field: await MultipartFile.fromFile(filePath),
      if (extraFields != null)
        ...extraFields.map((key, value) => MapEntry(key, value)),
    });
    return _dio.post(path, data: formData);
  }
}
