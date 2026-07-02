class ApiConstants {
  // Render Production Backend
  static const String baseUrl = 'https://vpay-flutter.onrender.com';

  // Local Development (uncomment for local testing)
  // static const String baseUrl = 'http://10.0.2.2:8000';  // Android Emulator
  // static const String baseUrl = 'http://localhost:8000'; // iOS Simulator/Web

  static String get enroll => '/enroll';
  static String get enrollStatus => '/enroll/status';
  static String get enrollReset => '/enroll/reset';

  // Face verification endpoints
  static String get faceEnroll => '/face/enroll';
  static String get faceVerify => '/face/verify';
  static String get faceStatus => '/face/status';
  static String get faceReset => '/face/reset';

  static String get verify => '/verify';
  static String get transcribe => '/transcribe';
  static String get parse => '/parse';
  static String get voicePayParse => '/voice-pay/parse';
  static String get voicePayConfirm => '/pay/intent/confirm';
  static String get paymentIntent => '/pay/intent';
  static String get pay => '/pay';
  static String get challenge => '/challenge';
  static String get challengeVerify => '/challenge/verify';
  static String get wallet => '/wallet';
  static String get transactions => '/wallet/transactions';
  static String get contacts => '/contacts';
  static String get qrParse => '/qr/parse';
  static String get health => '/health';
}
