class PaymentResponse {
  final bool success;
  final String message;
  final double newBalance;
  final int? transactionId;

  PaymentResponse({
    required this.success,
    required this.message,
    required this.newBalance,
    this.transactionId,
  });

  factory PaymentResponse.fromJson(Map<String, dynamic> json) => PaymentResponse(
        success: json['success'] as bool,
        message: json['message'] as String,
        newBalance: (json['new_balance'] as num).toDouble(),
        transactionId: json['transaction_id'] as int?,
      );
}
