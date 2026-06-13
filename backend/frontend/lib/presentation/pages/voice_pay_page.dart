import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

import '../blocs/voice_pay/voice_pay_bloc.dart';
import '../blocs/voice_pay/voice_pay_event.dart';
import '../blocs/voice_pay/voice_pay_state.dart';
import '../../core/utils/audio_recorder.dart';
import '../../core/services/tts_service.dart';

class VoicePayPage extends StatefulWidget {
  const VoicePayPage({super.key});

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
  bool _isListeningForConfirmation = false;
  bool _confirmationDetected = false;

  @override
  void initState() {
    super.initState();
    _initSpeechToText();
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

  void _startListeningForConfirmation() async {
    setState(() {
      _isListeningForConfirmation = true;
      _listenCountdown = 10;
      _confirmationDetected = false;
    });

    final available = await _speechToText.listen(
      onResult: (result) {
        setState(() {
          _lastSpokenPhrase = result.recognizedWords.toLowerCase();
        });
        print('Heard: $_lastSpokenPhrase');

        // Check for confirmation phrase in real-time
        if (_lastSpokenPhrase.contains('yes') &&
            (_lastSpokenPhrase.contains('confirm') || _lastSpokenPhrase.contains('payment'))) {
          _confirmationDetected = true;
          _stopListening();
          _stopRecording();
          print('✓ Confirmation phrase detected!');
        }
      },
      listenFor: const Duration(seconds: 10),
    );

    if (available) {
      // Countdown timer
      _countdownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
        if (_listenCountdown > 1 && !_confirmationDetected) {
          setState(() => _listenCountdown--);
        } else {
          timer.cancel();
          if (!_confirmationDetected) {
            _stopListening();
          }
        }
      });
    }
  }

  void _stopListening() {
    _speechToText.stop();
    _countdownTimer?.cancel();
    setState(() {
      _isListeningForConfirmation = false;
    });
  }

  Future<void> _announcePayment(String displayText, String confirmPrompt) async {
    if (_isAnnouncing) return;
    _isAnnouncing = true;

    setState(() {
      _isListeningForConfirmation = false;
    });

    // Announce payment details
    await _ttsService.speak(
      'Processing payment of $displayText. $confirmPrompt',
      onComplete: () {
        _isAnnouncing = false;
        // Auto-start recording for voice confirmation
        _startRecording();
        // Start listening for confirmation phrase
        _startListeningForConfirmation();
      },
    );
  }

  @override
  void dispose() {
    _countdownTimer?.cancel();
    _ttsService.dispose();
    _audioRecorder.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => VoicePayBloc(),
      child: Builder(
        builder: (context) {
          return Scaffold(
            appBar: AppBar(title: const Text('Voice Pay')),
            body: BlocListener<VoicePayBloc, VoicePayState>(
              listener: (context, state) {
                if (state is VoicePayConfirm) {
                  // Announce payment details and start listening
                  _announcePayment(state.displayText, state.confirmPrompt);
                }
              },
              child: BlocBuilder<VoicePayBloc, VoicePayState>(
                builder: (context, state) {
                  return Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        if (state is VoicePayInitial || state is VoicePayRecording)
                          _buildRecordingView(state),
                        if (state is VoicePayProcessing) _buildProcessingView(),
                        if (state is VoicePayConfirm) _buildConfirmationView(state),
                        if (state is VoicePayListening) _buildListeningView(state),
                        if (state is VoicePayVerifying) _buildVerifyingView(),
                        if (state is VoicePaySuccess) _buildSuccessView(state),
                        if (state is VoicePayError) _buildErrorView(state),
                      ],
                    ),
                  );
                },
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildRecordingView(VoicePayState state) {
    return Column(
      children: [
        const SizedBox(height: 40),
        Text(
          _isRecording ? 'Recording...' : 'Hold to Record',
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
        const SizedBox(height: 24),
        if (_isRecording)
          const Text(
            'Release to process',
            style: TextStyle(color: Colors.grey),
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

  Widget _buildConfirmationView(VoicePayConfirm state) {
    return Column(
      children: [
        const Icon(Icons.receipt_long, size: 64, color: Colors.blue),
        const SizedBox(height: 24),
        Text(
          'Payment Detected',
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        const SizedBox(height: 16),
        Card(
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
                const SizedBox(height: 12),
                if (_isAnnouncing) ...[
                  const CircularProgressIndicator(),
                  const SizedBox(height: 8),
                  Text(
                    'Announcing payment details...',
                    style: Theme.of(context).textTheme.bodyMedium,
                    textAlign: TextAlign.center,
                  ),
                ] else if (_isListeningForConfirmation) ...[
                  Icon(
                    Icons.mic,
                    color: _confirmationDetected ? Colors.green : Colors.orange,
                    size: 32,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Say "Yes, confirm the payment"',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: _confirmationDetected ? Colors.green : Colors.orange,
                          fontWeight: FontWeight.w500,
                        ),
                    textAlign: TextAlign.center,
                  ),
                  if (_confirmationDetected) ...[
                    const SizedBox(height: 8),
                    Text(
                      '✓ Detected: "${_lastSpokenPhrase}"',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Colors.green,
                          ),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ],
              ],
            ),
          ),
        ),
        const SizedBox(height: 32),
        if (_isListeningForConfirmation && !_confirmationDetected)
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
                    style: const TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                ],
              ),
            ),
          ),
        if (_lastSpokenPhrase.isNotEmpty && _isListeningForConfirmation && !_confirmationDetected) ...[
          const SizedBox(height: 24),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.grey.shade100,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Column(
              children: [
                const Text(
                  'Heard:',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                Text(
                  _lastSpokenPhrase,
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
                  style: const TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
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
                const Text(
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