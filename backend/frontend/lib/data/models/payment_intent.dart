class PaymentIntentRequest {
  final String recipient;
  final String upiId;
  final double amount;
  final String? note;
  final String? displayText;
  final String? confirmPrompt;

  PaymentIntentRequest({
    required this.recipient,
    required this.upiId,
    required this.amount,
    this.note,
    this.displayText,
    this.confirmPrompt,
  });

  Map<String, dynamic> toJson() => {
        'recipient': recipient,
        'upi_id': upiId,
        'amount': amount,
        if (note != null) 'note': note,
        if (displayText != null) 'display_text': displayText,
        if (confirmPrompt != null) 'confirm_prompt': confirmPrompt,
      };
}

class PaymentIntentResponse {
  final int intentId;
  final String displayText;
  final String confirmPrompt;
  final int expiresInSeconds;

  PaymentIntentResponse({
    required this.intentId,
    required this.displayText,
    required this.confirmPrompt,
    required this.expiresInSeconds,
  });

  factory PaymentIntentResponse.fromJson(Map<String, dynamic> json) =>
      PaymentIntentResponse(
        intentId: json['intent_id'] as int,
        displayText: json['display_text'] as String,
        confirmPrompt: json['confirm_prompt'] as String,
        expiresInSeconds: json['expires_in_seconds'] as int,
      );
}
