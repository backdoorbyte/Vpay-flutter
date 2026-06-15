import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

import '../../core/utils/permission_helper.dart';

class QrScanPage extends StatefulWidget {
  const QrScanPage({super.key});

  @override
  State<QrScanPage> createState() => _QrScanPageState();
}

class _QrScanPageState extends State<QrScanPage> {
  bool _hasPermission = false;
  bool _isProcessing = false;

  @override
  void initState() {
    super.initState();
    _checkPermission();
  }

  Future<void> _checkPermission() async {
    final granted = await PermissionHelper.requestCameraPermission();
    setState(() => _hasPermission = granted);
  }

  void _onDetect(BarcodeCapture capture) {
    // Prevent multiple scans while a dialog is already showing
    if (_isProcessing) return;

    final barcode = capture.barcodes.firstOrNull;
    if (barcode == null || barcode.rawValue == null) return;

    // Parse UPI QR string (upi://pay?pa=...&am=...&cu=INR&tn=...)
    final url = barcode.rawValue!;
    if (url.startsWith('upi://')) {
      _isProcessing = true;
      final upiId = _extractUPIId(url);
      final amount = _extractAmount(url);
      final payee = _extractPayee(url);
      final note = _extractNote(url);

      if (context.mounted) {
        showDialog(
          context: context,
          barrierDismissible: false,
          builder: (_) => AlertDialog(
            title: const Text('UPI QR Detected'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Payee: ${payee ?? upiId ?? 'Unknown'}'),
                if (amount != null) Text('Amount: ₹$amount'),
                if (note != null) Text('Note: $note'),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () {
                  _isProcessing = false;
                  Navigator.pop(context);
                },
                child: const Text('Cancel'),
              ),
              ElevatedButton(
                onPressed: () {
                  Navigator.pop(context);
                  // Navigate to payment with UPI details
                  context.push('/voice-pay', extra: {
                    'upiId': upiId,
                    'amount': amount,
                    'note': note,
                  });
                },
                child: const Text('Pay Now'),
              ),
            ],
          ),
        );
      }
    }
  }

  String? _extractUPIId(String url) {
    final match = RegExp(r'pa=([^&]+)').firstMatch(url);
    return match?.group(1);
  }

  String? _extractAmount(String url) {
    final match = RegExp(r'am=([^&]+)').firstMatch(url);
    return match?.group(1);
  }

  String? _extractPayee(String url) {
    final match = RegExp(r'pn=([^&]+)').firstMatch(url);
    if (match != null) {
      return Uri.decodeComponent(match.group(1)!);
    }
    return null;
  }

  String? _extractNote(String url) {
    final match = RegExp(r'tn=([^&]+)').firstMatch(url);
    if (match != null) {
      return Uri.decodeComponent(match.group(1)!);
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Scan QR Code')),
      body: _hasPermission
          ? MobileScanner(
              onDetect: _onDetect,
              overlay: Container(
                decoration: BoxDecoration(
                  border: Border.all(
                    color: Theme.of(context).colorScheme.primary,
                    width: 2,
                  ),
                  borderRadius: BorderRadius.circular(20),
                ),
              ),
            )
          : Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.camera_alt, size: 64, color: Colors.grey),
                  SizedBox(height: 16),
                  Text('Camera permission required to scan QR codes'),
                  SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: _checkPermission,
                    child: Text('Grant Permission'),
                  ),
                ],
              ),
            ),
    );
  }
}
