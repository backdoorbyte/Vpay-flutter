import 'package:flutter/foundation.dart';
import 'package:flutter_tts/flutter_tts.dart';

class TextToSpeechService {
  bool _isSpeaking = false;

  Future<void> speak(String text, {Function()? onComplete}) async {
    if (kIsWeb) {
      // Web doesn't support flutter_tts, skip silently
      print('[TTS] Web platform detected, skipping TTS: $text');
      onComplete?.call();
      return;
    }

    try {
      final flutterTts = FlutterTts();
      await flutterTts.setSharedInstance(true);
      await flutterTts.setLanguage('en-US');
      await flutterTts.setPitch(1.0);
      await flutterTts.setSpeechRate(0.5);

      _isSpeaking = true;
      await flutterTts.speak(text);

      flutterTts.setCompletionHandler(() {
        _isSpeaking = false;
        onComplete?.call();
      });
    } catch (e) {
      print('[TTS] Error: $e');
      onComplete?.call();
    }
  }

  Future<void> stop() async {
    if (kIsWeb) return;
    try {
      final flutterTts = FlutterTts();
      await flutterTts.stop();
      _isSpeaking = false;
    } catch (e) {
      print('[TTS] Stop error: $e');
    }
  }

  Future<bool> isSpeaking() async => _isSpeaking;

  void dispose() {
    if (!kIsWeb) {
      FlutterTts().stop();
    }
  }
}