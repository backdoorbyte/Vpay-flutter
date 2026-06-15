import '../../core/constants/api_constants.dart';
import '../../core/network/api_client.dart';
import '../models/contact.dart';

class ContactsRepository {
  final ApiClient _apiClient;

  ContactsRepository({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  Future<List<Contact>> getContacts() async {
    final response = await _apiClient.get(ApiConstants.contacts);
    final data = response.data as Map<String, dynamic>;
    final list = data['contacts'] as List<dynamic>;
    return list.map((e) => Contact.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Contact> createContact(ContactCreateRequest request) async {
    final response = await _apiClient.post(ApiConstants.contacts, data: request.toJson());
    return Contact.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> deleteContact(int contactId) async {
    await _apiClient.delete('${ApiConstants.contacts}/$contactId');
  }
}
