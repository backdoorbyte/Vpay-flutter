import 'parsed_command.dart';

class VoicePayResponse {
  final String transcribedText;
  final String displayText;
  final String confirmPrompt;
  final String language;
  final ParsedCommand parsed;
  final bool needsUpi;

  VoicePayResponse({
    required this.transcribedText,
    this.displayText = '',
    this.confirmPrompt = '',
    required this.language,
    required this.parsed,
    this.needsUpi = false,
  });

  factory VoicePayResponse.fromJson(Map<String, dynamic> json) =>
      VoicePayResponse(
        transcribedText: json['transcribed_text'] as String,
        displayText: json['display_text'] as String? ?? '',
        confirmPrompt: json['confirm_prompt'] as String? ?? '',
        language: json['language'] as String,
        parsed: ParsedCommand.fromJson(json['parsed'] as Map<String, dynamic>),
        needsUpi: json['needs_upi'] as bool? ?? false,
      );
}
