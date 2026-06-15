import 'package:flutter/material.dart';

import 'app.dart';
import 'injection.dart';
import 'router.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initDependencies();
  setupAuthListener();
  runApp(const VPayApp());
}