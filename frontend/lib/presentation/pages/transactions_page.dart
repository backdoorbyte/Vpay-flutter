import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';

import '../../injection.dart';
import '../blocs/wallet/wallet_bloc.dart';
import '../blocs/wallet/wallet_event.dart';
import '../blocs/wallet/wallet_state.dart' as ws;

class TransactionsPage extends StatelessWidget {
  const TransactionsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider.value(
      value: getIt<WalletBloc>(),
      child: const _TransactionsView(),
    );
  }
}

class _TransactionsView extends StatelessWidget {
  const _TransactionsView();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Transaction History')),
      body: BlocBuilder<WalletBloc, ws.WalletState>(
        builder: (context, state) {
          if (state is ws.WalletLoading) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state is ws.WalletError) {
            return Center(child: Text('Error: ${state.message}'));
          }
          if (state is ws.WalletLoaded && state.transactions.isEmpty) {
            return const Center(child: Text('No transactions yet'));
          }
          if (state is ws.WalletLoaded) {
            return ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: state.transactions.length,
              itemBuilder: (context, index) {
                final tx = state.transactions[index];
                return Card(
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor: Colors.green[100],
                      child: Icon(Icons.arrow_downward, color: Colors.green[700]),
                    ),
                    title: Text(tx.recipient),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (tx.upiId != null) Text(tx.upiId!),
                        Text(
                          DateFormat.yMMMd().format(DateTime.parse(tx.createdAt)),
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                    trailing: Text(
                      '-₹${tx.amount.toStringAsFixed(2)}',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            color: Colors.red,
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                  ),
                );
              },
            );
          }
          return const SizedBox.shrink();
        },
      ),
    );
  }
}