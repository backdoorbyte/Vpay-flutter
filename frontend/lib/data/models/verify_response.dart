class VerifyResponse {
  final bool verified;
  final double score;
  final double threshold;
  final String message;

  VerifyResponse({
    required this.verified,
    required this.score,
    required this.threshold,
    required this.message,
  });

  factory VerifyResponse.fromJson(Map<String, dynamic> json) => VerifyResponse(
        verified: json['verified'] as bool,
        score: (json['score'] as num).toDouble(),
        threshold: (json['threshold'] as num).toDouble(),
        message: json['message'] as String,
      );
}
