import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../blocs/enroll/enroll_bloc.dart';
import '../blocs/enroll/enroll_event.dart';
import '../blocs/enroll/enroll_state.dart';
import '../../core/utils/audio_recorder.dart';

class EnrollPage extends StatefulWidget {
  const EnrollPage({super.key});

  @override
  State<EnrollPage> createState() => _EnrollPageState();
}

class _EnrollPageState extends State<EnrollPage> {
  final AudioRecorderService _audioRecorder = AudioRecorderService();
  bool _isRecording = false;

  // Cache the last known enrollment status so the UI stays visible
  // even when the Bloc is in intermediate states like EnrollRecording.
  int _samplesReceived = 0;
  int _samplesRequired = 20; // Matches backend REQUIRED_SAMPLES
  bool _isEnrolled = false;

  @override
  void initState() {
    super.initState();
    context.read<EnrollBloc>().add(CheckEnrollStatus());
  }

  void _startRecording() async {
    setState(() => _isRecording = true);
    await _audioRecorder.startRecording();
    context.read<EnrollBloc>().add(StartEnrollRecording());
  }

  void _stopRecording() async {
    setState(() => _isRecording = false);
    String? path;
    try {
      path = await _audioRecorder.stopRecording();
    } catch (e) {
      print('[EnrollPage] Error stopping recording: $e');
    }
    if (path != null) {
      context.read<EnrollBloc>().add(SubmitEnrollSample(path));
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Recording failed — please try again.')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Voice Enrollment')),
      body: BlocListener<EnrollBloc, EnrollState>(
        // Cache enrollment status whenever a full-status state arrives
        // so intermediate states (EnrollRecording, EnrollLoading) can still render.
        listenWhen: (_, current) => current is EnrollStatusLoaded || current is EnrollSuccess,
        listener: (context, state) {
          if (state is EnrollStatusLoaded) {
            _samplesReceived = state.samplesReceived;
            _samplesRequired = state.samplesRequired;
            _isEnrolled = state.isEnrolled;
          } else if (state is EnrollSuccess) {
            _samplesReceived = state.samplesReceived;
            _isEnrolled = state.isEnrolled;
          }
        },
        child: BlocBuilder<EnrollBloc, EnrollState>(
          builder: (context, state) {
            // Read sample counts directly from the current state so they
            // update the instant the backend returns the new stats.
            final int samplesReceived;
            final int samplesRequired;
            final bool isEnrolled;

            if (state is EnrollStatusLoaded) {
              samplesReceived = state.samplesReceived;
              samplesRequired = state.samplesRequired;
              isEnrolled = state.isEnrolled;
            } else if (state is EnrollSuccess) {
              samplesReceived = state.samplesReceived;
              samplesRequired = _samplesRequired; // keep cached required
              isEnrolled = state.isEnrolled;
            } else {
              samplesReceived = _samplesReceived;
              samplesRequired = _samplesRequired;
              isEnrolled = _isEnrolled;
            }

            final showRecordingUi = (state is EnrollStatusLoaded && !state.isEnrolled) ||
                                    state is EnrollRecording ||
                                    (state is EnrollError && !isEnrolled);
            final showSuccessUi = (state is EnrollStatusLoaded && state.isEnrolled) ||
                                  (state is EnrollSuccess && state.isEnrolled);

            return Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                children: [
                  const SizedBox(height: 20),

                  // Progress indicator (reads latest state values)
                  if (!isEnrolled)
                    _buildProgressCard(samplesReceived, samplesRequired),
                  const SizedBox(height: 30),

                  // Loading / checking status
                  if (state is EnrollInitial || state is EnrollLoading)
                    const Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          CircularProgressIndicator(),
                          SizedBox(height: 16),
                          Text('Loading enrollment status...'),
                        ],
                      ),
                    ),

                  // Recording UI
                  if (showRecordingUi) ...[
                    GestureDetector(
                      onTapDown: (_) => _startRecording(),
                      onTapUp: (_) => _stopRecording(),
                      onTapCancel: () => setState(() => _isRecording = false),
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 200),
                        width: _isRecording ? 140 : 120,
                        height: _isRecording ? 140 : 120,
                        decoration: BoxDecoration(
                          color: _isRecording ? Colors.red : Theme.of(context).colorScheme.primary,
                          borderRadius: BorderRadius.circular(_isRecording ? 70 : 60),
                          boxShadow: [
                            BoxShadow(
                              color: (_isRecording ? Colors.red : Colors.black)
                                  .withValues(alpha: 0.2),
                              blurRadius: 20,
                              spreadRadius: 5,
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
                    const SizedBox(height: 20),
                    Text(
                      _isRecording ? 'Recording...' : 'Tap & Hold to Record',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Read any paragraph for 3-5 seconds',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: Colors.grey[600],
                          ),
                      textAlign: TextAlign.center,
                    ),
                  ],

                  // Success UI
                  if (showSuccessUi) ...[
                    const Icon(Icons.check_circle, size: 80, color: Colors.green),
                    const SizedBox(height: 16),
                    Text(
                      'Voice Enrolled!',
                      style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                            color: Colors.green,
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Your voice profile is active',
                      style: Theme.of(context).textTheme.bodyLarge,
                    ),
                  ],

                  // Error UI
                  if (state is EnrollError) ...[
                    const Spacer(),
                    const Icon(Icons.error_outline, size: 64, color: Colors.red),
                    const SizedBox(height: 16),
                    Text(
                      'Something went wrong',
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                            color: Colors.red,
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      state.message,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: Colors.grey[600],
                          ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton.icon(
                      onPressed: () => context.read<EnrollBloc>().add(CheckEnrollStatus()),
                      icon: const Icon(Icons.refresh),
                      label: const Text('Try Again'),
                    ),
                  ],

                  const Spacer(),

                  // Reset button
                  if (showSuccessUi)
                    OutlinedButton.icon(
                      onPressed: () => context.read<EnrollBloc>().add(ResetEnrollment()),
                      icon: const Icon(Icons.refresh),
                      label: const Text('Reset Enrollment'),
                    ),
                  const SizedBox(height: 20),
                ],
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildProgressCard(int current, int required) {
    final progress = current / required;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Progress: $current / $required samples',
                    style: Theme.of(context).textTheme.titleMedium),
                Text('${(progress * 100).toInt()}%',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          color: Theme.of(context).colorScheme.primary,
                        )),
              ],
            ),
            const SizedBox(height: 12),
            ClipRRect(
              borderRadius: BorderRadius.circular(10),
              child: LinearProgressIndicator(
                value: progress,
                minHeight: 8,
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _audioRecorder.dispose();
    super.dispose();
  }
}