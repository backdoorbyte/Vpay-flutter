class Transaction {
  final int id;
  final String recipient;
  final String? upiId;
  final double amount;
  final String? note;
  final String status;
  final double? verificationScore;
  final String createdAt;

  Transaction({
    required this.id,
    required this.recipient,
    this.upiId,
    required this.amount,
    this.note,
    required this.status,
    this.verificationScore,
    required this.createdAt,
  });

  factory Transaction.fromJson(Map<String, dynamic> json) => Transaction(
        id: json['id'] as int,
        recipient: json['recipient'] as String,
        upiId: json['upi_id'] as String?,
        amount: (json['amount'] as num).toDouble(),
        note: json['note'] as String?,
        status: json['status'] as String,
        verificationScore: json['verification_score'] != null
            ? (json['verification_score'] as num).toDouble()
            : null,
        createdAt: json['created_at'] as String,
      );
}
