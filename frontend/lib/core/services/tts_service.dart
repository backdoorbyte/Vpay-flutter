import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter_tts/flutter_tts.dart';

class TextToSpeechService {
  bool _isSpeaking = false;

  Future<void> speak(String text, {Function()? onComplete, String language = 'en'}) async {
    if (kIsWeb) {
      onComplete?.call();
      return;
    }

    try {
      final flutterTts = FlutterTts();
      await flutterTts.setSharedInstance(true);
      // Use selected language (en-US or hi-IN for Hindi)
      // For Hindi, we still use English TTS for better handling of mixed Hinglish text
      final ttsLanguage = language == 'hi' ? 'en-IN' : 'en-US';
      await flutterTts.setLanguage(ttsLanguage);
      await flutterTts.setPitch(1.0);
      await flutterTts.setSpeechRate(0.5);

      // Safety fallback in case the completion handler never fires
      Timer? safetyTimer;
      safetyTimer = Timer(const Duration(seconds: 10), () {
        _isSpeaking = false;
        onComplete?.call();
      });

      _isSpeaking = true;

      flutterTts.setCompletionHandler(() {
        _isSpeaking = false;
        safetyTimer?.cancel();
        onComplete?.call();
      });

      await flutterTts.speak(text);
    } catch (e) {
      print('[TTS] Error: $e');
      _isSpeaking = false;
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
      // ignore: discarded_futures
      FlutterTts().stop();
    }
  }
}
