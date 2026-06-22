import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../blocs/auth/auth_bloc.dart';
import '../blocs/auth/auth_event.dart';
import '../blocs/auth/auth_state.dart' as wsAuth;
import '../blocs/wallet/wallet_bloc.dart';
import '../blocs/wallet/wallet_event.dart';
import '../blocs/wallet/wallet_state.dart' as ws;

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  @override
  void initState() {
    super.initState();
    context.read<WalletBloc>().add(FetchWallet());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              _buildHeader(),
              const SizedBox(height: 24),

              // Wallet Card
              BlocBuilder<WalletBloc, ws.WalletState>(
                builder: (context, state) {
                  if (state is ws.WalletLoading) {
                    return _buildShimmerCard();
                  }
                  return _buildWalletCard(state);
                },
              ),
              const SizedBox(height: 24),

              // Quick Actions
              const Text(
                'Quick Actions',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1f2937),
                ),
              ),
              const SizedBox(height: 16),
              _buildQuickActionsRow(),
              const SizedBox(height: 16),
              _buildQuickActionsRowSecond(),

              const SizedBox(height: 24),

              // Voice Enrollment Promo
              _buildVoiceEnrollCard(),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF2e4af4), Color(0xFF6366f1), Color(0xFF8b5cf6)],
        ),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Welcome back,',
                  style: TextStyle(fontSize: 12, color: Colors.white70),
                ),
                const SizedBox(height: 4),
                BlocBuilder<AuthBloc, wsAuth.AuthState>(
                  builder: (context, state) {
                    final name = state is wsAuth.AuthAuthenticated
                        ? state.email?.split('@').first ?? 'User'
                        : 'User';
                    return Text(
                      name,
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    );
                  },
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.logout, color: Colors.white),
            onPressed: () => context.read<AuthBloc>().add(AuthSignedOut()),
          ),
        ],
      ),
    );
  }

  Widget _buildWalletCard(ws.WalletState walletState) {
    final isLoaded = walletState is ws.WalletLoaded;
    final wallet = isLoaded ? (walletState).wallet : null;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF2e4af4), Color(0xFF4f46e5), Color(0xFF6366f1)],
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF2e4af4).withAlpha(102),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white.withAlpha(51),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(Icons.account_balance_wallet, color: Colors.white, size: 24),
              ),
              const SizedBox(width: 12),
              const Expanded(
                child: Text(
                  'Your Wallet',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500, color: Colors.white),
                ),
              ),
              if (isLoaded)
                Chip(
                  avatar: Icon(
                    wallet!.isVoiceEnrolled ? Icons.verified : Icons.voice_over_off,
                    size: 14,
                    color: wallet.isVoiceEnrolled ? Colors.green : Colors.orange,
                  ),
                  label: Text(
                    wallet.isVoiceEnrolled ? 'Voice Active' : 'Voice Off',
                    style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600),
                  ),
                  backgroundColor: wallet.isVoiceEnrolled
                      ? Colors.green.withAlpha(26)
                      : Colors.orange.withAlpha(26),
                  padding: EdgeInsets.zero,
                  materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  visualDensity: VisualDensity.compact,
                ),
            ],
          ),
          const SizedBox(height: 20),
          const Text(
            'Balance',
            style: TextStyle(fontSize: 12, color: Colors.white70, fontWeight: FontWeight.w500),
          ),
          const SizedBox(height: 8),
          Text(
            isLoaded ? '₹${wallet!.balance.toStringAsFixed(2)}' : '₹0.00',
            style: const TextStyle(
              fontSize: 36,
              fontWeight: FontWeight.bold,
              color: Colors.white,
              letterSpacing: -1,
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.white.withAlpha(51),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.account_balance, color: Colors.white, size: 16),
                    SizedBox(width: 6),
                    Text('VPay', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.white)),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildShimmerCard() {
    return Container(
      height: 180,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(20),
        gradient: LinearGradient(colors: [Colors.grey[300]!, Colors.grey[200]!, Colors.grey[300]!]),
      ),
    );
  }

  Widget _buildQuickActionsRow() {
    return Row(
      children: [
        Expanded(
          child: _QuickActionTile(
            icon: Icons.mic_rounded,
            label: 'Voice Pay',
            color: const Color(0xFF2e4af4),
            onTap: () => context.push('/voice-pay'),
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: _QuickActionTile(
            icon: Icons.qr_code_scanner_rounded,
            label: 'Scan QR',
            color: const Color(0xFF06b6d4),
            onTap: () => context.push('/qr-scan'),
          ),
        ),
      ],
    );
  }

  Widget _buildQuickActionsRowSecond() {
    return Row(
      children: [
        Expanded(
          child: _QuickActionTile(
            icon: Icons.contacts_rounded,
            label: 'Contacts',
            color: const Color(0xFF10b981),
            onTap: () => context.push('/contacts'),
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: _QuickActionTile(
            icon: Icons.history_rounded,
            label: 'History',
            color: const Color(0xFFF59E0B),
            onTap: () => context.push('/transactions'),
          ),
        ),
      ],
    );
  }

  Widget _buildVoiceEnrollCard() {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () => context.push('/enroll'),
        borderRadius: BorderRadius.circular(20),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF06b6d4), Color(0xFF3b82f6), Color(0xFF6366f1)],
            ),
            borderRadius: BorderRadius.circular(20),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF6366f1).withAlpha(76),
                blurRadius: 15,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white.withAlpha(51),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: const Icon(Icons.record_voice_over, color: Colors.white, size: 28),
              ),
              const SizedBox(width: 14),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Voice Enrollment',
                      style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
                    ),
                    SizedBox(height: 4),
                    Text(
                      'Enable voice payments for secure transactions',
                      style: TextStyle(fontSize: 11, color: Colors.white, height: 1.2),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Text(
                  'Start',
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF4f46e5)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _QuickActionTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  const _QuickActionTile({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(20),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: Colors.grey[200]!, width: 1),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withAlpha(5),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Column(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  gradient: LinearGradient(colors: [color, color.withOpacity(0.7)]),
                  borderRadius: BorderRadius.circular(14),
                  boxShadow: [
                    BoxShadow(
                      color: color.withAlpha(76),
                      blurRadius: 10,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: Icon(icon, color: Colors.white, size: 24),
              ),
              const SizedBox(height: 12),
              Text(
                label,
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1f2937),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}