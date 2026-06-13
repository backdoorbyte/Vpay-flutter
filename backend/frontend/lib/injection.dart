import 'package:get_it/get_it.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../core/network/api_client.dart';
import '../data/repositories/auth_repository.dart';
import '../data/repositories/contacts_repository.dart';
import '../data/repositories/enroll_repository.dart';
import '../data/repositories/voice_pay_repository.dart';
import '../data/repositories/wallet_repository.dart';
import '../presentation/blocs/auth/auth_bloc.dart';
import '../presentation/blocs/contacts/contacts_bloc.dart';
import '../presentation/blocs/enroll/enroll_bloc.dart';
import '../presentation/blocs/voice_pay/voice_pay_bloc.dart';
import '../presentation/blocs/wallet/wallet_bloc.dart';

final getIt = GetIt.instance;

Future<void> initDependencies() async {
  // Initialize Supabase
  await Supabase.initialize(
    url: 'https://qmuwykzbkcxabljiezsn.supabase.co',
    publishableKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFtdXd5a3pia2N4YWJsamllenNuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA5MzQyNTgsImV4cCI6MjA5NjUxMDI1OH0.wko4CN8MNQfWX2kKmKxmzX0a1ZxcHzu7-Nr1fhDw45M',
    debug: false,
  );

  // Core
  getIt.registerLazySingleton<ApiClient>(() => ApiClient());

  // Repositories
  getIt.registerLazySingleton<AuthRepository>(() => AuthRepository());
  getIt.registerLazySingleton<WalletRepository>(() => WalletRepository(apiClient: getIt()));
  getIt.registerLazySingleton<VoicePayRepository>(() => VoicePayRepository(apiClient: getIt()));
  getIt.registerLazySingleton<ContactsRepository>(() => ContactsRepository(apiClient: getIt()));
  getIt.registerLazySingleton<EnrollRepository>(() => EnrollRepository(apiClient: getIt()));

  // BLoCs
  getIt.registerFactory<AuthBloc>(() => AuthBloc(authRepository: getIt()));
  getIt.registerFactory<WalletBloc>(() => WalletBloc(walletRepository: getIt()));
  getIt.registerFactory<VoicePayBloc>(() => VoicePayBloc(voicePayRepository: getIt()));
  getIt.registerFactory<ContactsBloc>(() => ContactsBloc(contactsRepository: getIt()));
  getIt.registerFactory<EnrollBloc>(() => EnrollBloc(enrollRepository: getIt()));
}