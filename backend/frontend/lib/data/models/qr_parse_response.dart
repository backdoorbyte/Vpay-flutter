class QrParseResponse {
  final String upiId;
  final String? payeeName;
  final double? amount;
  final String? note;
  final String rawPayload;

  QrParseResponse({
    required this.upiId,
    this.payeeName,
    this.amount,
    this.note,
    required this.rawPayload,
  });

  factory QrParseResponse.fromJson(Map<String, dynamic> json) => QrParseResponse(
        upiId: json['upi_id'] as String,
        payeeName: json['payee_name'] as String?,
        amount: json['amount'] != null ? (json['amount'] as num).toDouble() : null,
        note: json['note'] as String?,
        rawPayload: json['raw_payload'] as String,
      );
}
