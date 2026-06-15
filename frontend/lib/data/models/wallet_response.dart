class WalletResponse {
  final double balance;
  final bool isVoiceEnrolled;
  final String userName;

  WalletResponse({
    required this.balance,
    required this.isVoiceEnrolled,
    required this.userName,
  });

  factory WalletResponse.fromJson(Map<String, dynamic> json) => WalletResponse(
        balance: (json['balance'] as num).toDouble(),
        isVoiceEnrolled: json['is_voice_enrolled'] as bool,
        userName: json['user_name'] as String,
      );
}
