import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../data/models/transaction.dart' as tx;
import '../../../data/repositories/wallet_repository.dart';
import 'wallet_event.dart' as we;
import 'wallet_state.dart' as ws;

class WalletBloc extends Bloc<we.WalletEvent, ws.WalletState> {
  final WalletRepository _walletRepository;

  WalletBloc({WalletRepository? walletRepository})
      : _walletRepository = walletRepository ?? WalletRepository(),
        super(ws.WalletInitial()) {
    on<we.FetchWallet>(_onFetchWallet);
    on<we.TransactionsLoaded>(_onFetchTransactions);
  }

  Future<void> _onFetchWallet(we.FetchWallet event, Emitter<ws.WalletState> emit) async {
    emit(ws.WalletLoading());
    try {
      final wallet = await _walletRepository.getWallet();
      List<tx.Transaction> transactions = [];
      try {
        transactions = await _walletRepository.getTransactions();
      } catch (_) {
        // Transactions are optional
      }
      emit(ws.WalletLoaded(wallet: wallet, transactions: transactions));
    } catch (e) {
      emit(ws.WalletError(message: e.toString()));
    }
  }

  Future<void> _onFetchTransactions(we.TransactionsLoaded event, Emitter<ws.WalletState> emit) async {
    // Handled as part of fetch
  }
}
