import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

import '../blocs/voice_pay/voice_pay_bloc.dart';
import '../blocs/voice_pay/voice_pay_event.dart';
import '../blocs/voice_pay/voice_pay_state.dart';
import '../../core/utils/audio_recorder.dart';
import '../../core/services/tts_service.dart';
import '../blocs/wallet/wallet_bloc.dart';
import '../blocs/wallet/wallet_event.dart';

/// Phases of the confirmation screen so the UI stays on one page.
enum _ConfirmPhase { idle, announcing, recording, timeout }

class VoicePayPage extends StatefulWidget {
  final String? initialUpiId;
  final double? initialAmount;
  final String? initialNote;

  const VoicePayPage({
    this.initialUpiId,
    this.initialAmount,
    this.initialNote,
    super.key,
  });

  @override
  State<VoicePayPage> createState() => _VoicePayPageState();
}

class _VoicePayPageState extends State<VoicePayPage> {
  final AudioRecorderService _audioRecorder = AudioRecorderService();
  final TextToSpeechService _ttsService = TextToSpeechService();
  final stt.SpeechToText _speechToText = stt.SpeechToText();

  bool _isRecording = false;
  int _listenCountdown = 10;
  Timer? _countdownTimer;
  String _lastSpokenPhrase = '';
  bool _isAnnouncing = false;

  // ---- Confirmation flow state ----
  _ConfirmPhase _confirmPhase = _ConfirmPhase.idle;
  double _recordingProgress = 1.0;
  Timer? _recordingTimer;
  String? _recordedAudioPath;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initSpeechToText();
      if (widget.initialUpiId != null) {
        context.read<VoicePayBloc>().add(SetQrData(
          upiId: widget.initialUpiId,
          amount: widget.initialAmount,
          note: widget.initialNote,
        ));
      }
    });
  }

  Future<void> _initSpeechToText() async {
    await _speechToText.initialize(
      onError: (error) => print('Speech recognition error: $error'),
      onStatus: (status) {
        print('Speech status: $status');
        if (status == 'done' || status == 'notListening') {
          _stopListening();
        }
      },
    );
  }

  void _startRecording() {
    setState(() => _isRecording = true);
    context.read<VoicePayBloc>().add(StartRecording());
  }

  void _stopRecording() {
    setState(() => _isRecording = false);
    context.read<VoicePayBloc>().add(StopRecording());
  }

  void _stopListening() {
    _speechToText.stop();
    _countdownTimer?.cancel();
  }

  // ─────────────────── Confirmation helpers ───────────────────

  /// Converts the backend display text into a TTS-friendly sentence.
  String _buildTtsText(String displayText, String language) {
    // Extract amount (digits after ₹ / Rs / rupees / rupaye / rupya / rupay)
    final amountMatch = RegExp(r'[₹R\s]*([\d,]+)\s*(?:rs|rs\.|rupees?|rupaye?|rupya|rupay|रुपये?|रु\.?)?').firstMatch(displayText);
    final amount = amountMatch?.group(1) ?? '';

    // Extract recipient (everything after "to ")
    final recipientMatch = RegExp(r'to\s+(.+)').firstMatch(displayText);
    String rawRecipient = recipientMatch?.group(1)?.trim() ?? '';

    // Fix "Rahul" pronunciation
    String ttsRecipient = rawRecipient
        .replaceAll('Rahul', 'Rah-hul')
        .replaceAll('rahul', 'Rah-hul');

    // Handle @ and domain pronunciation
    final atIndex = ttsRecipient.indexOf('@');
    if (atIndex != -1) {
      String name = ttsRecipient.substring(0, atIndex);
      String domain = ttsRecipient.substring(atIndex + 1);

      // Fix name again in case it was split
      name = name
          .replaceAll('Rahul', 'Rah-hul')
          .replaceAll('rahul', 'Rah-hul');

      // If the name part is numeric (e.g., phone number), spell out digits
      if (name.isNotEmpty && int.tryParse(name) != null) {
        name = name.split('').join(' ');
      }

      String ttsDomain;
      if (domain.toLowerCase().contains('bank')) {
        // Pronounce as word:
        // axisbank → axis bank, icicibank → icici bank
        ttsDomain = domain.replaceAllMapped(
          RegExp(r'bank', caseSensitive: false),
          (match) => ' bank',
        );
      } else {
        // Spell as individual letters: ybl → y b l
        ttsDomain = domain.toUpperCase().split('').join(' ');
      }

      ttsRecipient = '$name at the rate $ttsDomain';
    }

    if (language == 'hi') {
      return 'Payment confirm karne ke liye, "हाँ, payment confirm karo" boliye';
    }
    return 'Please say, "yes confirm the payment", to pay $amount Rupees to $ttsRecipient';
  }

  /// Called once when Bloc enters [VoicePayConfirm].
  void _announcePayment(String displayText, String language) {
    if (_isAnnouncing) return;
    _isAnnouncing = true;

    setState(() => _confirmPhase = _ConfirmPhase.announcing);

    // Build TTS text in the detected language for confirmation prompt
    String ttsText;
    if (language == 'hi') {
      // Extract amount for Hindi TTS
      final amountMatch = RegExp(r'[₹R\s]*([\d,]+)\s*(?:rs|rs\.|rupees?|rupaye?|rupya|rupay|रुपये?|रु\.?)?').firstMatch(displayText);
      final amount = amountMatch?.group(1) ?? '';

      // Extract recipient
      final recipientMatch = RegExp(r'to\s+(.+)').firstMatch(displayText);
      String rawRecipient = recipientMatch?.group(1)?.trim() ?? '';

      // Fix "Rahul" pronunciation in Hindi
      String ttsRecipient = rawRecipient
          .replaceAll('Rahul', 'Rah-hul')
          .replaceAll('rahul', 'Rah-hul');

      // Handle @ and domain pronunciation for Hindi
      final atIndex = ttsRecipient.indexOf('@');
      if (atIndex != -1) {
        String name = ttsRecipient.substring(0, atIndex);
        String domain = ttsRecipient.substring(atIndex + 1);

        name = name
            .replaceAll('Rahul', 'Rah-hul')
            .replaceAll('rahul', 'Rah-hul');

        if (name.isNotEmpty && int.tryParse(name) != null) {
          name = name.split('').join(' ');
        }

        String ttsDomain;
        if (domain.toLowerCase().contains('bank')) {
          ttsDomain = domain.replaceAllMapped(
            RegExp(r'bank', caseSensitive: false),
            (match) => ' bank',
          );
        } else {
          ttsDomain = domain.toUpperCase().split('').join(' ');
        }

        ttsRecipient = '$name at the rate $ttsDomain';
      }

      ttsText = '$amount rupaye $ttsRecipient bhejne ke liye, haan bol kar payment ki pushti karein';
    } else {
      // English TTS
      ttsText = _buildTtsText(displayText, 'en');
    }

    print('[TTS] Speaking: $ttsText (language: $language)');

    _ttsService.speak(
      ttsText,
      language: language,
      onComplete: () {
        _isAnnouncing = false;
        // After agent finishes speaking → auto-start confirmation recording
        _startConfirmationRecording();
      },
    );
  }

  /// Called when Bloc enters [VoicePayNeedsAmount].
  void _announceAmountPrompt(String upiId) {
    final ttsText = 'How much do you want to pay to $upiId?';
    print('[TTS] Speaking: $ttsText');
    _ttsService.speak(ttsText, language: 'en');
  }

  /// Starts the 10-second confirmation recording.
  Future<void> _startConfirmationRecording() async {
    if (_confirmPhase == _ConfirmPhase.recording) return;

    setState(() {
      _confirmPhase = _ConfirmPhase.recording;
      _recordingProgress = 1.0;
      _lastSpokenPhrase = '';
    });

    // Start audio recording (page-level recorder — separate from BLoC)
    try {
      _recordedAudioPath = await _audioRecorder.startRecording();
      print('[Confirmation] Recording started: $_recordedAudioPath');
    } catch (e) {
      print('[Confirmation] Error starting recording: $e');
    }

    // 10-second countdown (updated every 100 ms for smooth animation)
    _recordingTimer?.cancel();
    _recordingTimer = Timer.periodic(const Duration(milliseconds: 100), (timer) {
      setState(() => _recordingProgress -= 0.01);
      if (_recordingProgress <= 0) {
        timer.cancel();
        _handleConfirmationTimeout();
      }
    });

    // NOTE: speech_to_text is NOT used here because on Android only one
    // audio source can be active at a time. The recorder already holds the
    // mic, so STT silently fails. Instead, we record the full 10 seconds
    // and send the audio to the backend, which uses Whisper (far more
    // accurate) to check for confirmation phrases.
  }

  /// Send the recorded confirmation audio to the backend for verification.
  /// Called when the user taps 'Done' or when the 10-second timer expires.
  Future<void> _submitConfirmationAudio() async {
    if (_isSubmitting) return;
    _isSubmitting = true;
    _recordingTimer?.cancel();

    String? path;
    try {
      path = await _audioRecorder.stopRecording();
    } catch (e) {
      print('[Confirmation] Error stopping recorder: $e');
    }

    if (path != null) {
      print('[Confirmation] Submitting audio: $path');
      context.read<VoicePayBloc>().add(SubmitVoiceConfirmation(path));
    } else {
      // Fallback: no audio file → show timeout UI
      setState(() => _confirmPhase = _ConfirmPhase.timeout);
      Future.delayed(const Duration(seconds: 3), () {
        if (mounted) {
          context.read<VoicePayBloc>().add(CancelPayment());
        }
      });
    }
  }

  void _handleConfirmationTimeout() async {
    _recordingTimer?.cancel();

    // When timer expires, ALWAYS send the audio to the backend.
    // Backend's Whisper will check if user said "yes/confirm".
    String? path;
    try {
      path = await _audioRecorder.stopRecording();
    } catch (e) {
      print('[Confirmation] Error stopping recorder on timeout: $e');
    }

    if (path != null) {
      print('[Confirmation] Timer expired, submitting audio for verification');
      context.read<VoicePayBloc>().add(SubmitVoiceConfirmation(path));
    } else {
      // No audio captured
      setState(() => _confirmPhase = _ConfirmPhase.timeout);
      Future.delayed(const Duration(seconds: 3), () {
        if (mounted) {
          context.read<VoicePayBloc>().add(CancelPayment());
        }
      });
    }
  }

  @override
  void dispose() {
    _countdownTimer?.cancel();
    _recordingTimer?.cancel();
    _ttsService.dispose();
    _audioRecorder.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Voice Pay')),
      body: BlocConsumer<VoicePayBloc, VoicePayState>(
        listenWhen: (previous, current) =>
            current is VoicePayConfirm ||
            current is VoicePayNeedsAmount ||
            current is VoicePaySuccess,
        listener: (context, state) {
          if (state is VoicePayConfirm) {
            _announcePayment(state.displayText, state.language);
          }
          if (state is VoicePayNeedsAmount) {
            _announceAmountPrompt(state.upiId);
          }
          if (state is VoicePaySuccess) {
            // Refresh wallet balance after successful payment
            try {
              context.read<WalletBloc>().add(FetchWallet());
            } catch (_) {
              // WalletBloc not available in this context
            }
          }
        },
        builder: (context, state) {
          return SingleChildScrollView(
            physics: const ClampingScrollPhysics(),
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (state is VoicePayInitial || state is VoicePayRecording)
                    _buildRecordingView(state),
                  if (state is VoicePayProcessing) _buildProcessingView(),
                  if (state is VoicePayConfirm) _buildConfirmationView(state),
                  if (state is VoicePayNeedsAmount)
                    _buildNeedsAmountView(state),
                  if (state is VoicePayListening) _buildListeningView(state),
                  if (state is VoicePayVerifying) _buildVerifyingView(),
                  if (state is VoicePaySuccess) _buildSuccessView(state),
                  if (state is VoicePayError) _buildErrorView(state),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  // ─────────────────── QR: Ask for amount view ───────────────────

  Widget _buildNeedsAmountView(VoicePayNeedsAmount state) {
    return Column(
      children: [
        const SizedBox(height: 40),
        const Icon(Icons.qr_code, size: 64, color: Colors.blue),
        const SizedBox(height: 16),
        Text(
          'How much to pay?',
          style: Theme.of(context).textTheme.headlineSmall,
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 8),
        Text(
          'UPI ID: ${state.upiId}',
          style: Theme.of(context).textTheme.bodyLarge?.copyWith(
            color: Colors.grey[600],
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 16),
        Text(
          'Hold the mic and say the amount',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: Colors.grey[600],
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 40),
        GestureDetector(
          onTapDown: (_) => _startRecording(),
          onTapUp: (_) => _stopRecording(),
          onTapCancel: () {
            setState(() => _isRecording = false);
            context.read<VoicePayBloc>().add(StopRecording());
          },
          child: RepaintBoundary(
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              width: _isRecording ? 140 : 120,
              height: _isRecording ? 140 : 120,
              decoration: BoxDecoration(
                color: _isRecording ? Colors.red : Theme.of(context).colorScheme.primary,
                borderRadius: BorderRadius.circular(_isRecording ? 70 : 60),
                boxShadow: _isRecording
                    ? [
                        BoxShadow(
                          color: Colors.red.withValues(alpha: 0.4),
                          blurRadius: 30,
                          spreadRadius: 10,
                        ),
                      ]
                    : [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.1),
                          blurRadius: 10,
                          offset: const Offset(0, 4),
                        ),
                      ],
              ),
              child: Icon(
                _isRecording ? Icons.stop : Icons.mic,
                size: 50,
                color: Colors.white,
              ),
            ),
          ),
        ),
      ],
    );
  }

  // ─────────────────── Recording view (English UI always) ───────────────────

  Widget _buildRecordingView(VoicePayState state) {
    return Column(
      children: [
        const SizedBox(height: 40),
        Text(
          _isRecording ? 'Recording...' : 'Tap and hold to record',
          style: Theme.of(context).textTheme.headlineSmall,
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 8),
        Text(
          _isRecording
              ? 'Say something like "Pay Rahul 500 rupees"'
              : 'Tap and hold the mic button to record',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Colors.grey[600]),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 40),
        GestureDetector(
          onTapDown: (_) => _startRecording(),
          onTapUp: (_) => _stopRecording(),
          onTapCancel: () {
            setState(() => _isRecording = false);
            context.read<VoicePayBloc>().add(StopRecording());
          },
          child: RepaintBoundary(
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              width: _isRecording ? 140 : 120,
              height: _isRecording ? 140 : 120,
              decoration: BoxDecoration(
                color: _isRecording ? Colors.red : Theme.of(context).colorScheme.primary,
                borderRadius: BorderRadius.circular(_isRecording ? 70 : 60),
                boxShadow: _isRecording
                    ? [
                        BoxShadow(
                          color: Colors.red.withValues(alpha: 0.4),
                          blurRadius: 30,
                          spreadRadius: 10,
                        ),
                      ]
                    : [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.1),
                          blurRadius: 10,
                          offset: const Offset(0, 4),
                        ),
                      ],
              ),
              child: Icon(
                _isRecording ? Icons.stop : Icons.mic,
                size: 50,
                color: Colors.white,
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildProcessingView() {
    return const Column(
      children: [
        SizedBox(height: 40),
        CircularProgressIndicator(),
        SizedBox(height: 24),
        Text('Processing your voice...'),
      ],
    );
  }

  // ─────────────── Confirmation view (single page, 3 phases) ───────────────

  Widget _buildConfirmationView(VoicePayConfirm state) {
    return Column(
      children: [
        const SizedBox(height: 16),
        const Icon(Icons.receipt_long, size: 64, color: Colors.blue),
        const SizedBox(height: 16),
        Text(
          'Confirm Payment',
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        const SizedBox(height: 16),

        // Payment summary card (shown in all phases)
        RepaintBoundary(
          child: Card(
            color: Colors.blue.shade50,
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  Text(
                    state.displayText,
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          ),
        ),
        const SizedBox(height: 24),

        // Phase-dependent content
        if (_confirmPhase == _ConfirmPhase.announcing) ..._buildAnnouncingPhase(),
        if (_confirmPhase == _ConfirmPhase.recording) ..._buildRecordingPhase(state),
        if (_confirmPhase == _ConfirmPhase.timeout) ..._buildTimeoutPhase(),
        if (_confirmPhase == _ConfirmPhase.idle) ..._buildIdlePhase(),
      ],
    );
  }

  List<Widget> _buildAnnouncingPhase() {
    return [
      const SizedBox(height: 16),
      const CircularProgressIndicator(),
      const SizedBox(height: 12),
      Text(
        'Agent is speaking...',
        style: Theme.of(context).textTheme.bodyMedium,
        textAlign: TextAlign.center,
      ),
      const SizedBox(height: 12),
      TextButton.icon(
        onPressed: () {
          _isAnnouncing = false;
          _ttsService.stop().then((_) => _startConfirmationRecording());
        },
        icon: const Icon(Icons.skip_next),
        label: const Text('Skip'),
      ),
    ];
  }

  List<Widget> _buildRecordingPhase(VoicePayConfirm state) {
    return [
      const SizedBox(height: 8),
      Text(
        'Say "Yes, confirm the payment"',
        style: Theme.of(context).textTheme.titleMedium?.copyWith(
          fontWeight: FontWeight.w600,
        ),
        textAlign: TextAlign.center,
      ),
      const SizedBox(height: 24),
      _buildFancyMic(),
      const SizedBox(height: 16),
      if (_lastSpokenPhrase.isNotEmpty)
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.grey.shade100,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(
            'Heard: "$_lastSpokenPhrase"',
            style: Theme.of(context).textTheme.bodyMedium,
            textAlign: TextAlign.center,
          ),
        ),
      const SizedBox(height: 8),
      // Allow the user to tap the mic to submit early once they've spoken
      Text(
        'Tap the mic when done speaking',
        style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.grey[600]),
        textAlign: TextAlign.center,
      ),
      const SizedBox(height: 12),
      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          ElevatedButton.icon(
            onPressed: _submitConfirmationAudio,
            icon: const Icon(Icons.check_circle),
            label: const Text('Done'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.green.shade600,
              foregroundColor: Colors.white,
            ),
          ),
          const SizedBox(width: 16),
          OutlinedButton.icon(
            onPressed: () {
              _recordingTimer?.cancel();
              _audioRecorder.stopRecording().catchError((_) => null);
              context.read<VoicePayBloc>().add(CancelPayment());
            },
            icon: const Icon(Icons.cancel, color: Colors.red),
            label: const Text('Cancel', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    ];
  }

  List<Widget> _buildTimeoutPhase() {
    // Announce payment declined in the detected language (from state)
    // TTS is bilingual, UI text stays in English
    _ttsService.speak(
      'Payment declined. No voice detected within 10 seconds.',
      language: 'en',
      onComplete: () {}
    );

    return [
      const SizedBox(height: 24),
      const Icon(Icons.cancel, size: 64, color: Colors.red),
      const SizedBox(height: 16),
      Text(
        'Payment Declined',
        style: Theme.of(context).textTheme.headlineSmall?.copyWith(color: Colors.red),
        textAlign: TextAlign.center,
      ),
      const SizedBox(height: 8),
      Text(
        'No voice was detected within 10 seconds.',
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Colors.grey[600]),
        textAlign: TextAlign.center,
      ),
    ];
  }

  List<Widget> _buildIdlePhase() {
    return [
      const SizedBox(height: 16),
      Text(
        'Please wait...',
        style: Theme.of(context).textTheme.bodyMedium,
        textAlign: TextAlign.center,
      ),
    ];
  }

  /// Fancy mic with animated countdown ring.
  Widget _buildFancyMic() {
    return Stack(
      alignment: Alignment.center,
      children: [
        // Outer pulsing ring
        Container(
          width: 200,
          height: 200,
          decoration: BoxDecoration(
            color: Colors.red.withValues(alpha: 0.08),
            shape: BoxShape.circle,
          ),
        ),
        // Circular progress countdown
        SizedBox(
          width: 160,
          height: 160,
          child: CircularProgressIndicator(
            value: _recordingProgress.clamp(0.0, 1.0),
            strokeWidth: 6,
            backgroundColor: Colors.grey[300],
            valueColor: AlwaysStoppedAnimation<Color>(Colors.red.shade400),
          ),
        ),
        // Mic button with gradient (tappable for early submit)
        GestureDetector(
          onTap: _submitConfirmationAudio,
          child: Container(
            width: 120,
            height: 120,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [Colors.red.shade400, Colors.red.shade700],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: Colors.red.withValues(alpha: 0.35),
                  blurRadius: 20,
                  spreadRadius: 4,
                ),
              ],
            ),
            child: const Icon(
              Icons.mic,
              size: 50,
              color: Colors.white,
            ),
          ),
        ),
        // Countdown badge
        Positioned(
          bottom: 0,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
            decoration: BoxDecoration(
              color: Colors.red.shade700,
              borderRadius: BorderRadius.circular(20),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.15),
                  blurRadius: 6,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Text(
              '${(_recordingProgress * 10).ceil()}s',
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildListeningView(VoicePayListening state) {
    return Column(
      children: [
        const SizedBox(height: 40),
        Text(
          'Listening for confirmation...',
          style: Theme.of(context).textTheme.headlineSmall,
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 8),
        Text(
          'Say "Yes, confirm the payment"',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Colors.grey[600]),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 40),
        Container(
          width: 120,
          height: 120,
          decoration: BoxDecoration(
            color: Colors.red,
            shape: BoxShape.circle,
            boxShadow: [
              BoxShadow(
                color: Colors.red.withValues(alpha: 0.4),
                blurRadius: 30,
                spreadRadius: 10,
              ),
            ],
          ),
          child: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.mic, size: 40, color: Colors.white),
                const SizedBox(height: 8),
                Text(
                  '$_listenCountdown',
                  style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 24),
        Text(
          'seconds remaining',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        if (state.transcript?.isNotEmpty ?? false) ...[
          const SizedBox(height: 24),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.grey.shade100,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Column(
              children: [
                Text(
                  'Heard:',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                Text(
                  state.transcript!,
                  style: Theme.of(context).textTheme.bodyLarge,
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }

  Widget _buildVerifyingView() {
    return const Column(
      children: [
        SizedBox(height: 40),
        CircularProgressIndicator(),
        SizedBox(height: 24),
        Text('Verifying voice...'),
        SizedBox(height: 8),
        Text(
          'Matching voiceprint with enrolled profile',
          style: TextStyle(color: Colors.grey),
        ),
      ],
    );
  }

  Widget _buildSuccessView(VoicePaySuccess state) {
    // Announce payment success in the detected language
    final language = state.result.language;
    String successMessage;
    if (language == 'hi') {
      successMessage = 'Payment safal hua! Aapka payment pura kar diya gaya.';
    } else {
      successMessage = 'Payment successful! Your payment has been completed.';
    }

    _ttsService.speak(
      successMessage,
      language: language,
      onComplete: () {}
    );

    return Column(
      children: [
        const Icon(Icons.check_circle, size: 80, color: Colors.green),
        const SizedBox(height: 24),
        Text(
          'Payment Successful!',
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
            color: Colors.green,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 12),
        Text(
          state.result.message,
          style: Theme.of(context).textTheme.bodyLarge,
          textAlign: TextAlign.center,
        ),
        if (state.result.newBalance != null)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text(
              'New Balance: ₹${state.result.newBalance!.toStringAsFixed(2)}',
              style: Theme.of(context).textTheme.titleMedium,
            ),
          ),
        const SizedBox(height: 32),
        ElevatedButton(
          onPressed: () {
            context.read<VoicePayBloc>().add(ResetPayment());
          },
          child: const Text('Make Another Payment'),
        ),
      ],
    );
  }

  Widget _buildErrorView(VoicePayError state) {
    return Column(
      children: [
        const Icon(Icons.error_outline, size: 64, color: Colors.red),
        const SizedBox(height: 24),
        Text(
          'Error',
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(color: Colors.red),
        ),
        const SizedBox(height: 12),
        Text(
          state.message,
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 32),
        ElevatedButton(
          onPressed: () {
            context.read<VoicePayBloc>().add(ResetPayment());
          },
          child: const Text('Try Again'),
        ),
      ],
    );
  }
}