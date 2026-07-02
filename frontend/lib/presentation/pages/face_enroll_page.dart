import 'dart:async';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:permission_handler/permission_handler.dart';

import '../../../injection.dart';
import '../../../core/services/face_verification_service.dart';
import '../blocs/face_enroll/face_enroll_bloc.dart';
import '../blocs/face_enroll/face_enroll_event.dart';
import '../blocs/face_enroll/face_enroll_state.dart';

class FaceEnrollPage extends StatefulWidget {
  const FaceEnrollPage({super.key});

  @override
  State<FaceEnrollPage> createState() => _FaceEnrollPageState();
}

class _FaceEnrollPageState extends State<FaceEnrollPage> {
  late FaceEnrollBloc _bloc;

  // Camera state - managed locally, not rebuilt by BLoC
  FaceVerificationService? _faceService;
  bool _isPermissionGranted = false;
  bool _isCameraReady = false;
  String? _errorMessage;
  CameraController? _cameraController;

  @override
  void initState() {
    super.initState();
    _bloc = getIt<FaceEnrollBloc>();
    _bloc.add(FaceEnrollInitialize());
    // Initialize camera after first frame
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initCamera();
    });
  }

  Future<void> _initCamera() async {
    try {
      final status = await Permission.camera.request();

      if (!mounted) return;

      if (status.isGranted) {
        setState(() => _isPermissionGranted = true);

        _faceService = getIt<FaceVerificationService>();
        await _faceService!.initializeCamera();

        _cameraController = _faceService!.cameraController;

        // Add listener for camera ready state
        if (_cameraController != null) {
          if (_cameraController!.value.isInitialized) {
            setState(() => _isCameraReady = true);
          }
          _cameraController!.addListener(() {
            if (mounted && _cameraController!.value.isInitialized) {
              setState(() => _isCameraReady = true);
            }
          });
        }
      } else {
        setState(() {
          _errorMessage = status.isPermanentlyDenied
              ? 'Camera permission permanently denied. Enable in Settings.'
              : 'Camera permission denied.';
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _errorMessage = 'Camera init failed: $e');
      }
      print('[FaceEnroll] Camera init error: $e');
    }
  }

  @override
  void dispose() {
    _cameraController?.removeListener(() {});
    _faceService?.dispose();
    _bloc.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider<FaceEnrollBloc>(
      create: (_) => _bloc,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Face Enrollment'),
          backgroundColor: Colors.indigo,
          foregroundColor: Colors.white,
        ),
        body: Column(
          children: [
            // Status card - rebuilds on BLoC state
            BlocBuilder<FaceEnrollBloc, FaceEnrollState>(
              builder: (context, state) => _buildStatusCard(state),
            ),

            // Camera preview - uses current state, doesn't rebuild on BLoC changes
            Padding(
              padding: const EdgeInsets.all(16),
              child: _buildCameraPreview(),
            ),

            // Action button - rebuilds on BLoC state
            BlocBuilder<FaceEnrollBloc, FaceEnrollState>(
              builder: (context, state) => _buildActionButton(state),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusCard(FaceEnrollState state) {
    String statusText;
    IconData statusIcon;
    Color statusColor;

    if (state is FaceEnrollStatusLoaded) {
      statusText = state.isFaceEnrolled ? 'Face enrolled' : 'Not enrolled';
      statusIcon = state.isFaceEnrolled ? Icons.check_circle : Icons.person_outline;
      statusColor = state.isFaceEnrolled ? Colors.green : Colors.orange;
    } else if (state is FaceEnrollSuccess) {
      statusText = state.message;
      statusIcon = Icons.check_circle;
      statusColor = Colors.green;
    } else if (state is FaceEnrollError) {
      statusText = state.message;
      statusIcon = Icons.error;
      statusColor = Colors.red;
    } else if (state is FaceEnrollLoading) {
      statusText = 'Processing...';
      statusIcon = Icons.hourglass_empty;
      statusColor = Colors.blue;
    } else {
      statusText = 'Ready to enroll';
      statusIcon = Icons.person_outline;
      statusColor = Colors.grey;
    }

    return Card(
      margin: const EdgeInsets.all(16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(statusIcon, color: statusColor, size: 32),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Face Verification', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 4),
                  Text(statusText, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: statusColor)),
                ],
              ),
            ),
            if (state is FaceEnrollStatusLoaded && state.isFaceEnrolled)
              IconButton(
                icon: const Icon(Icons.refresh),
                onPressed: () => _bloc.add(FaceEnrollReset()),
                tooltip: 'Reset enrollment',
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildCameraPreview() {
    // Permission not granted yet
    if (!_isPermissionGranted) {
      return Container(
        margin: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.red[50],
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.red, width: 2),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.videocam_off, size: 64, color: Colors.red[400]),
            const SizedBox(height: 16),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Text(
                _errorMessage ?? 'Camera permission required',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.red[700], fontSize: 14),
              ),
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: _initCamera,
              icon: const Icon(Icons.refresh),
              label: const Text('Grant Permission'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.red[600],
                foregroundColor: Colors.white,
              ),
            ),
          ],
        ),
      );
    }

    // Camera initializing
    if (!_isCameraReady || _cameraController == null) {
      print('[FaceEnroll] Camera preview: initializing (ready=$_isCameraReady, controller=${_cameraController != null})');
      return Container(
        margin: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.grey[200],
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.indigo, width: 2),
        ),
        child: const Center(child: CircularProgressIndicator()),
      );
    }

    // Camera ready - show preview directly without FittedBox
    print('[FaceEnroll] Camera preview: rendering (initialized=${_cameraController!.value.isInitialized})');
    return Container(
      width: 300,
      height: 300,
      decoration: BoxDecoration(
        color: Colors.black,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.indigo, width: 2),
      ),
      clipBehavior: Clip.antiAlias,
      child: CameraPreview(_cameraController!),
    );
  }

  Widget _buildActionButton(FaceEnrollState state) {
    final isLoading = state is FaceEnrollLoading;
    final isEnrolled = (state is FaceEnrollStatusLoaded && state.isFaceEnrolled) ||
        state is FaceEnrollSuccess;

    return Container(
      padding: const EdgeInsets.all(24),
      child: ElevatedButton.icon(
        onPressed: !isLoading && _isCameraReady && _isPermissionGranted
            ? () => _bloc.add(FaceEnrollCapture())
            : null,
        icon: isLoading
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : const Icon(Icons.camera_alt),
        label: Text(isEnrolled ? 'Re-enroll Face' : 'Enroll Face'),
        style: ElevatedButton.styleFrom(
          backgroundColor: _isCameraReady && _isPermissionGranted ? Colors.indigo : Colors.grey[400],
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      ),
    );
  }
}