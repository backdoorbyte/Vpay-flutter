class EnrollResponse {
  final bool success;
  final String message;
  final int samplesReceived;
  final int samplesRequired;
  final bool enrolled;

  EnrollResponse({
    required this.success,
    required this.message,
    required this.samplesReceived,
    this.samplesRequired = 20,
    this.enrolled = false,
  });

  factory EnrollResponse.fromJson(Map<String, dynamic> json) => EnrollResponse(
        success: json['success'] as bool,
        message: json['message'] as String,
        samplesReceived: json['samples_received'] as int,
        samplesRequired: json['samples_required'] as int? ?? 20,
        enrolled: json['enrolled'] as bool? ?? false,
      );
}

class EnrollStatusResponse {
  final int samplesReceived;
  final int samplesRequired;
  final bool isVoiceEnrolled;
  final bool pendingInSession;

  EnrollStatusResponse({
    required this.samplesReceived,
    required this.samplesRequired,
    required this.isVoiceEnrolled,
    required this.pendingInSession,
  });

  factory EnrollStatusResponse.fromJson(Map<String, dynamic> json) =>
      EnrollStatusResponse(
        samplesReceived: json['samples_received'] as int,
        samplesRequired: json['samples_required'] as int,
        isVoiceEnrolled: json['is_voice_enrolled'] as bool,
        pendingInSession: json['pending_in_session'] as bool,
      );
}
