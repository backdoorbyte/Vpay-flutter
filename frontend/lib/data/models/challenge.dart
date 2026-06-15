class ChallengeResponse {
  final int challengeId;
  final String phrase;
  final int expiresInSeconds;

  ChallengeResponse({
    required this.challengeId,
    required this.phrase,
    required this.expiresInSeconds,
  });

  factory ChallengeResponse.fromJson(Map<String, dynamic> json) =>
      ChallengeResponse(
        challengeId: json['challenge_id'] as int,
        phrase: json['phrase'] as String,
        expiresInSeconds: json['expires_in_seconds'] as int,
      );
}

class ChallengeVerifyResponse {
  final bool verified;
  final double score;
  final double phraseMatchScore;
  final String transcribedText;
  final double threshold;
  final double limit;
  final bool refined;
  final String message;

  ChallengeVerifyResponse({
    required this.verified,
    required this.score,
    this.phraseMatchScore = 0.0,
    this.transcribedText = '',
    required this.threshold,
    this.limit = 0.0,
    this.refined = false,
    required this.message,
  });

  factory ChallengeVerifyResponse.fromJson(Map<String, dynamic> json) =>
      ChallengeVerifyResponse(
        verified: json['verified'] as bool,
        score: (json['score'] as num).toDouble(),
        phraseMatchScore: (json['phrase_match_score'] as num?)?.toDouble() ?? 0.0,
        transcribedText: json['transcribed_text'] as String? ?? '',
        threshold: (json['threshold'] as num).toDouble(),
        limit: (json['limit'] as num?)?.toDouble() ?? 0.0,
        refined: json['refined'] as bool? ?? false,
        message: json['message'] as String,
      );
}
