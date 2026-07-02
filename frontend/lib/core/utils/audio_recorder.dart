import 'dart:io';

import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

class AudioRecorderService {
  final AudioRecorder _recorder = AudioRecorder();
  String? _currentPath;

  Future<String?> startRecording() async {
    try {
      // Check permissions first
      final hasPermission = await _recorder.hasPermission();
      if (!hasPermission) {
        throw Exception('Microphone permission not granted. Please grant permission in app settings.');
      }

      // Get the app's cache directory (reliable across Android versions)
      final directory = await getApplicationCacheDirectory();
      await directory.create(recursive: true);

      // Create file path with a unique name
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final fileName = 'vpay_$timestamp.wav';
      _currentPath = '${directory.path}/$fileName';

      print('[AudioRecorder] Starting recording to: $_currentPath');
      print('[AudioRecorder] Directory exists: ${await directory.exists()}');

      // Start recording in WAV (raw PCM) for maximum backend compatibility
      await _recorder.start(const RecordConfig(
        encoder: AudioEncoder.wav,
        sampleRate: 16000,
        numChannels: 1,
      ), path: _currentPath!);

      // Give the file a moment to be created
      await Future.delayed(const Duration(milliseconds: 100));

      print('[AudioRecorder] Recording started');
      return _currentPath;
    } catch (e) {
      print('[AudioRecorder] Error starting recording: $e');
      rethrow;
    }
  }

  Future<String?> stopRecording() async {
    try {
      print('[AudioRecorder] Stopping recording...');
      final path = await _recorder.stop();
      print('[AudioRecorder] Stop returned: $path');

      // Use the path we tracked, as _recorder.stop() might return null on some platforms
      final actualPath = path ?? _currentPath;

      if (actualPath == null) {
        throw StateError('No recording path available');
      }

      print('[AudioRecorder] Verifying file at: $actualPath');

      // Wait a bit for the file to be flushed to disk (MediaCodec/MPEG4Writer needs time)
      await Future.delayed(const Duration(milliseconds: 300));

      // Verify file exists with retries (in case of slow I/O)
      final file = File(actualPath);
      for (int attempt = 0; attempt < 5; attempt++) {
        final exists = await file.exists();
        if (exists) {
          final length = await file.length();
          print('[AudioRecorder] File exists, size: $length bytes');
          if (length == 0) {
            print('[AudioRecorder] WARNING: File is empty, waiting...');
            await Future.delayed(const Duration(milliseconds: 200));
            continue;
          }
          _currentPath = null;
          return actualPath;
        }
        print('[AudioRecorder] File not found yet (attempt ${attempt + 1}/5), waiting...');
        await Future.delayed(const Duration(milliseconds: 200));
      }

      // File still not found after retries
      print('[AudioRecorder] ERROR: File does not exist at $actualPath after 5 attempts');
      // List directory contents to debug
      try {
        final dir = await getApplicationCacheDirectory();
        print('[AudioRecorder] Cache dir contents:');
        await for (final entry in dir.list()) {
          print('  - ${entry.path}');
        }
      } catch (e) {
        print('[AudioRecorder] Could not list directory: $e');
      }
      throw StateError('Recording file not found. Please try again.');
    } catch (e) {
      print('[AudioRecorder] Error stopping recording: $e');
      rethrow;
    }
  }

  void dispose() {
    _recorder.dispose();
    _currentPath = null;
  }
}