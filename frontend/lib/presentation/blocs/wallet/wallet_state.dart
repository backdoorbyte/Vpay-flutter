import 'package:equatable/equatable.dart';

import '../../../data/models/transaction.dart' as tx;
import '../../../data/models/wallet_response.dart';

abstract class WalletState extends Equatable {
  @override
  List<Object?> get props => [];
}

class WalletInitial extends WalletState {}

class WalletLoading extends WalletState {}

class WalletLoaded extends WalletState {
  final WalletResponse wallet;
  final List<tx.Transaction> transactions;

  WalletLoaded({required this.wallet, this.transactions = const []});

  @override
  List<Object?> get props => [wallet, transactions];
}

class WalletError extends WalletState {
  final String message;

  WalletError({required this.message});

  @override
  List<Object?> get props => [message];
}
