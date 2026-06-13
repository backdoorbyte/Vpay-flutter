import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../data/repositories/auth_repository.dart';
import '../injection.dart';
import '../presentation/blocs/auth/auth_bloc.dart';
import '../presentation/blocs/auth/auth_event.dart';
import '../presentation/blocs/enroll/enroll_bloc.dart';
import '../presentation/blocs/voice_pay/voice_pay_bloc.dart';
import '../presentation/blocs/wallet/wallet_bloc.dart';
import '../presentation/pages/contacts_page.dart';
import '../presentation/pages/enroll_page.dart';
import '../presentation/pages/home_page.dart';
import '../presentation/pages/login_page.dart';
import '../presentation/pages/qr_scan_page.dart';
import '../presentation/pages/transactions_page.dart';
import '../presentation/pages/voice_pay_page.dart';

final GlobalKey<NavigatorState> _rootNavigatorKey = GlobalKey<NavigatorState>();

// Notifier to trigger router refresh on auth state changes
final _authChangeNotifier = ValueNotifier<bool>(false);

final GoRouter router = GoRouter(
  navigatorKey: _rootNavigatorKey,
  initialLocation: '/login',
  refreshListenable: _authChangeNotifier,
  redirect: (context, state) {
    final authRepo = getIt<AuthRepository>();
    final isLoggedIn = authRepo.isLoggedIn;

    // Update notifier to trigger rebuild
    _authChangeNotifier.value = isLoggedIn;

    if (state.fullPath == '/login' || state.fullPath == '/') {
      if (isLoggedIn) return '/home';
      return null;
    }

    if (!isLoggedIn) {
      return '/login';
    }

    return null;
  },
  routes: [
    GoRoute(
      path: '/login',
      name: 'login',
      pageBuilder: (context, state) => MaterialPage(
        key: state.pageKey,
        child: BlocProvider(
          create: (_) => getIt<AuthBloc>()..add(AuthCheckRequested()),
          child: const LoginPage(),
        ),
      ),
    ),
    GoRoute(
      path: '/home',
      name: 'home',
      pageBuilder: (context, state) => MaterialPage(
        key: state.pageKey,
        child: MultiBlocProvider(
          providers: [
            BlocProvider(create: (_) => getIt<WalletBloc>()),
            BlocProvider(create: (_) => getIt<AuthBloc>()),
          ],
          child: const HomePage(),
        ),
      ),
    ),
    GoRoute(
      path: '/voice-pay',
      name: 'voicePay',
      pageBuilder: (context, state) => MaterialPage(
        key: state.pageKey,
        child: BlocProvider(
          create: (_) => getIt<VoicePayBloc>(),
          child: const VoicePayPage(),
        ),
      ),
    ),
    GoRoute(
      path: '/qr-scan',
      name: 'qrScan',
      pageBuilder: (context, state) => MaterialPage(
        key: state.pageKey,
        child: const QrScanPage(),
      ),
    ),
    GoRoute(
      path: '/contacts',
      name: 'contacts',
      pageBuilder: (context, state) => MaterialPage(
        key: state.pageKey,
        child: const ContactsPage(),
      ),
    ),
    GoRoute(
      path: '/enroll',
      name: 'enroll',
      pageBuilder: (context, state) => MaterialPage(
        key: state.pageKey,
        child: BlocProvider(
          create: (_) => getIt<EnrollBloc>(),
          child: const EnrollPage(),
        ),
      ),
    ),
    GoRoute(
      path: '/transactions',
      name: 'transactions',
      pageBuilder: (context, state) => MaterialPage(
        key: state.pageKey,
        child: const TransactionsPage(),
      ),
    ),
  ],
);

// Listen to Supabase auth changes and notify router
void setupAuthListener() {
  Supabase.instance.client.auth.onAuthStateChange.listen((data) {
    _authChangeNotifier.value = !(_authChangeNotifier.value);
  });
}