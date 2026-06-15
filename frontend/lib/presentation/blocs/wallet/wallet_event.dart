import 'package:equatable/equatable.dart';

abstract class WalletEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class FetchWallet extends WalletEvent {}

class TransactionsLoaded extends WalletEvent {}
