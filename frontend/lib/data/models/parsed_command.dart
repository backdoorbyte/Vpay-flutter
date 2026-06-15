class ParsedCommand {
  final String? recipient;
  final String? upiId;
  final double? amount;
  final String? note;
  final String rawText;
  final double confidence;
  final String resolution;

  ParsedCommand({
    this.recipient,
    this.upiId,
    this.amount,
    this.note,
    required this.rawText,
    this.confidence = 0.0,
    this.resolution = 'unknown',
  });

  factory ParsedCommand.fromJson(Map<String, dynamic> json) => ParsedCommand(
        recipient: json['recipient'] as String?,
        upiId: json['upi_id'] as String?,
        amount: json['amount'] != null ? (json['amount'] as num).toDouble() : null,
        note: json['note'] as String?,
        rawText: json['raw_text'] as String,
        confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
        resolution: json['resolution'] as String? ?? 'unknown',
      );
}
