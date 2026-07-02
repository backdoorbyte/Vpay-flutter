import 'dart:async';

import 'package:camera/camera.dart';

import '../../data/repositories/face_repository.dart';

/// Service for face verification using the device camera
class FaceVerificationService {
  CameraController? _cameraController;
  bool _isInitialized = false;
  bool _isDetecting = false;
  bool _isCapturing = false;
  DateTime? _lastCaptureTime;

  final FaceRepository _repository;

  FaceVerificationService(this._repository);

  /// Minimum time between captures to prevent main thread blocking (debounce)
  static const Duration _captureDebounceDuration = Duration(milliseconds: 500);

  /// Initialize the camera for face verification
  Future<void> initializeCamera() async {
    if (_isInitialized) return;

    try {
      final cameras = await availableCameras();
      final frontCamera = cameras.firstWhere(
        (camera) => camera.lensDirection == CameraLensDirection.front,
        orElse: () => cameras.first,
      );

      // Use low resolution for faster capture and reduced JPEG encoding work
      // This reduces main thread blocking during takePicture()
      _cameraController = CameraController(
        frontCamera,
        ResolutionPreset.low, // Changed from medium to low for performance
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.bgra8888,
      );

      await _cameraController!.initialize();
      _isInitialized = true;
      print('[FaceVerification] Camera initialized (low resolution)');
    } catch (e) {
      print('[FaceVerification] Camera initialization failed: $e');
      rethrow;
    }
  }

  /// Get the camera controller for preview widget
  CameraController? get cameraController => _cameraController;

  /// Check if camera is initialized
  bool get isInitialized => _isInitialized;

  /// Check if currently detecting
  bool get isDetecting => _isDetecting;

  /// Capture a single frame for face verification
  Future<FaceVerificationResult?> captureAndVerify({
    required int userId,
    double threshold = 0.6,
  }) async {
    if (!_isInitialized || _cameraController == null) {
      print('[FaceVerification] Camera not initialized');
      return null;
    }

    try {
      // Capture image
      final XFile image = await _cameraController!.takePicture();

      // Send to backend for verification
      final result = await _repository.verifyFace(
        image.path,
        userId: userId,
        threshold: threshold,
      );

      print('[FaceVerification] Verification result: ${result.verified} (${result.confidence})');
      return result;
    } catch (e) {
      print('[FaceVerification] Capture/verify failed: $e');
      return null;
    }
  }

  /// Start continuous face detection (captures frame every N seconds)
  /// Returns a stream of verification results
  Stream<FaceVerificationResult?> startContinuousDetection({
    required int userId,
    double threshold = 0.6,
    Duration interval = const Duration(seconds: 2),
  }) {
    final controller = StreamController<FaceVerificationResult?>.broadcast();

    if (!_isInitialized || _cameraController == null) {
      controller.addError('Camera not initialized');
      return controller.stream;
    }

    _isDetecting = true;

    Timer? timer;
    bool stopped = false;

    void tick() async {
      if (stopped || !_isDetecting) {
        controller.close();
        return;
      }

      final result = await captureAndVerify(userId: userId, threshold: threshold);
      if (!stopped) {
        controller.add(result);
      }
    }

    // First capture immediately
    tick();

    // Then capture at intervals
    timer = Timer.periodic(interval, (_) => tick());

    // Store timer reference for cleanup
    _detectionTimer = timer;

    return controller.stream;
  }

  Timer? _detectionTimer;

  /// Stop continuous detection
  void stopContinuousDetection() {
    _isDetecting = false;
    _detectionTimer?.cancel();
    _detectionTimer = null;
    print('[FaceVerification] Stopped continuous detection');
  }

  /// Capture and enroll a face with debouncing to prevent main thread blocking
  Future<bool> enrollFace({required int userId}) async {
    if (!_isInitialized || _cameraController == null) {
      print('[FaceVerification] Camera not initialized');
      return false;
    }

    // Debounce: prevent rapid capture calls that block the main thread
    final now = DateTime.now();
    if (_lastCaptureTime != null) {
      final elapsed = now.difference(_lastCaptureTime!);
      if (elapsed < _captureDebounceDuration) {
        print('[FaceVerification] Capture debounced (${elapsed.inMilliseconds}ms since last)');
        return false;
      }
    }

    // Prevent concurrent capture requests
    if (_isCapturing) {
      print('[FaceVerification] Capture already in progress');
      return false;
    }

    try {
      _isCapturing = true;
      _lastCaptureTime = now;

      // Capture image - this is heavy (JPEG encoding), but unavoidable
      // The low resolution preset helps reduce the work
      final XFile image = await _cameraController!.takePicture();

      // Yield to let the event loop process any pending UI updates
      await Future.delayed(Duration.zero);

      final success = await _repository.enrollFace(
        image.path,
        userId: userId,
      );

      print('[FaceVerification] Enrollment result: $success');
      return success;
    } catch (e) {
      print('[FaceVerification] Enrollment failed: $e');
      return false;
    } finally {
      _isCapturing = false;
    }
  }

  /// Dispose of camera resources
  void dispose() {
    stopContinuousDetection();
    _cameraController?.dispose();
    _cameraController = null;
    _isInitialized = false;
    print('[FaceVerification] Disposed');
  }
}