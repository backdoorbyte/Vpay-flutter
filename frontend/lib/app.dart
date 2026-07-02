import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'injection.dart';
import 'presentation/blocs/wallet/wallet_bloc.dart';
import 'router.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Bind scheduler to vsync for smooth rendering
  SchedulerBinding.instance.addPostFrameCallback((_) {
    debugPrint('App initialized with vsync');
  });

  // Initialize dependencies (Supabase, GetIt, repositories, BLoCs)
  await initDependencies();

  runApp(const VPayApp());
}

class VPayApp extends StatelessWidget {
  const VPayApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider.value(
          value: getIt<WalletBloc>(),
        ),
      ],
      child: MaterialApp.router(
        title: 'VPay',
        debugShowCheckedModeBanner: false,
        // Fix width=zero: ensure proper layout constraints
        builder: (context, child) {
          return MediaQuery(
            data: MediaQuery.of(context).copyWith(
              // Fix text scaling issues
              textScaler: TextScaler.noScaling,
            ),
            child: child!,
          );
        },
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: Colors.deepPurple,
            brightness: Brightness.light,
          ),
          useMaterial3: true,
          cardTheme: CardThemeData(
            elevation: 2,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
            ),
          ),
          inputDecorationTheme: InputDecorationTheme(
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
          ),
          elevatedButtonTheme: ElevatedButtonThemeData(
            style: ElevatedButton.styleFrom(
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              // Fix minimum button size to prevent layout issues
              minimumSize: const Size(64, 48),
            ),
          ),
        ),
        routerConfig: router,
      ),
    );
  }
}