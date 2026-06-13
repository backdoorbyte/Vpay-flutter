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

  @override
  void initState() {
    super.initState();
    context.read<EnrollBloc>().add(CheckEnrollStatus());
  }

  void _startRecording() async {
    setState(() => _isRecording = true);
    context.read<EnrollBloc>().add(StartEnrollRecording());
  }

  void _stopRecording() async {
    setState(() => _isRecording = false);
    final path = await _audioRecorder.stopRecording();
    if (path != null) {
      context.read<EnrollBloc>().add(SubmitEnrollSample(path));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Voice Enrollment')),
      body: BlocBuilder<EnrollBloc, EnrollState>(
        builder: (context, state) {
          return Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              children: [
                const SizedBox(height: 20),
                // Progress indicator
                if (state is EnrollStatusLoaded)
                  _buildProgressCard(state.samplesReceived, state.samplesRequired),
                const SizedBox(height: 30),
                // Show loading while checking status
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
                // Show recording UI when not enrolled
                if (state is EnrollStatusLoaded && !state.isEnrolled) ...[
                  GestureDetector(
                    onTapDown: (_) => _startRecording(),
                    onTapUp: (_) => _stopRecording(),
                    onTapCancel: () {
                      setState(() => _isRecording = false);
                    },
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 200),
                      width: _isRecording ? 140 : 120,
                      height: _isRecording ? 140 : 120,
                      decoration: BoxDecoration(
                        color: _isRecording ? Colors.red : Theme.of(context).colorScheme.primary,
                        borderRadius: BorderRadius.circular(_isRecording ? 70 : 60),
                        boxShadow: [
                          BoxShadow(
                            color: (_isRecording ? Colors.red : Colors.black).withValues(alpha: 0.2),
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
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Colors.grey[600]),
                    textAlign: TextAlign.center,
                  ),
                ],
                // Show success when enrolled
                if ((state is EnrollStatusLoaded && state.isEnrolled) ||
                    (state is EnrollSuccess && state.isEnrolled)) ...[
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
                const Spacer(),
                // Reset button (only when enrolled)
                if ((state is EnrollStatusLoaded && state.isEnrolled) ||
                    (state is EnrollSuccess && state.isEnrolled))
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