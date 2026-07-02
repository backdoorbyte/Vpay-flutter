import '../../core/constants/api_constants.dart';
import '../../core/network/api_client.dart';
import '../models/transaction.dart';
import '../models/wallet_response.dart';

class WalletRepository {
  final ApiClient _apiClient;

  WalletRepository({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  Future<WalletResponse> getWallet() async {
    final response = await _apiClient.get(ApiConstants.wallet);
    return WalletResponse.fromJson(response.data as Map<String, dynamic>);
  }

  Future<List<Transaction>> getTransactions() async {
    final response = await _apiClient.get(ApiConstants.transactions);
    final data = response.data as Map<String, dynamic>;
    final list = data['transactions'] as List<dynamic>;
    return list
        .map((e) => Transaction.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}
