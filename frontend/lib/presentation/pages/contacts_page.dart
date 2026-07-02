import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../injection.dart';
import '../blocs/contacts/contacts_bloc.dart';
import '../blocs/contacts/contacts_event.dart';
import '../blocs/contacts/contacts_state.dart';

class ContactsPage extends StatelessWidget {
  const ContactsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => getIt<ContactsBloc>()..add(FetchContacts()),
      child: const _ContactsView(),
    );
  }
}

class _ContactsView extends StatelessWidget {
  const _ContactsView();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Contacts')),
      body: BlocBuilder<ContactsBloc, ContactsState>(
        builder: (context, state) {
          if (state is ContactsLoading) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state is ContactsError) {
            return Center(child: Text('Error: ${state.message}'));
          }
          if (state is ContactsLoaded && state.contacts.isEmpty) {
            return const Center(child: Text('No contacts yet'));
          }
          if (state is ContactsLoaded) {
            return ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: state.contacts.length,
              itemBuilder: (context, index) {
                final contact = state.contacts[index];
                return Card(
                  child: ListTile(
                    leading: CircleAvatar(
                      child: Text(contact.name[0].toUpperCase()),
                    ),
                    title: Text(contact.name),
                    subtitle: Text(contact.upiId),
                    trailing: IconButton(
                      icon: const Icon(Icons.delete_outline),
                      onPressed: () {
                        context.read<ContactsBloc>().add(RemoveContact(contactId: contact.id));
                      },
                    ),
                  ),
                );
              },
            );
          }
          return const SizedBox.shrink();
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showAddContactDialog(context),
        child: const Icon(Icons.add),
      ),
    );
  }

  void _showAddContactDialog(BuildContext context) {
    final nameController = TextEditingController();
    final upiController = TextEditingController();
    final phoneController = TextEditingController();

    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Add Contact'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: nameController,
              decoration: const InputDecoration(hintText: 'Name'),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: upiController,
              decoration: const InputDecoration(hintText: 'UPI ID (e.g., user@ybl)'),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: phoneController,
              decoration: const InputDecoration(hintText: 'Phone (optional)'),
              keyboardType: TextInputType.phone,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              context.read<ContactsBloc>().add(AddContact(
                name: nameController.text.trim(),
                upiId: upiController.text.trim(),
                phone: phoneController.text.trim().isEmpty ? null : phoneController.text.trim(),
              ));
              Navigator.pop(context);
            },
            child: const Text('Add'),
          ),
        ],
      ),
    );
  }
}