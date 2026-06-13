class ConfirmVerifyResponse {
  final bool verified;
  final double score;
  final double threshold;
  final double limit;
  final bool refined;
  final String transcribedText;
  final String message;
  final bool paymentCompleted;
  final double? newBalance;
  final int? transactionId;
  final String responseText;

  ConfirmVerifyResponse({
    required this.verified,
    required this.score,
    required this.threshold,
    this.limit = 0.0,
    this.refined = false,
    this.transcribedText = '',
    required this.message,
    this.paymentCompleted = false,
    this.newBalance,
    this.transactionId,
    this.responseText = '',
  });

  factory ConfirmVerifyResponse.fromJson(Map<String, dynamic> json) =>
      ConfirmVerifyResponse(
        verified: json['verified'] as bool,
        score: (json['score'] as num).toDouble(),
        threshold: (json['threshold'] as num).toDouble(),
        limit: (json['limit'] as num?)?.toDouble() ?? 0.0,
        refined: json['refined'] as bool? ?? false,
        transcribedText: json['transcribed_text'] as String? ?? '',
        message: json['message'] as String,
        paymentCompleted: json['payment_completed'] as bool? ?? false,
        newBalance: json['new_balance'] != null
            ? (json['new_balance'] as num).toDouble()
            : null,
        transactionId: json['transaction_id'] as int?,
        responseText: json['response_text'] as String? ?? '',
      );
}
