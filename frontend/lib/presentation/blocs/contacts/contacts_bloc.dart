import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../data/models/contact.dart';
import '../../../data/repositories/contacts_repository.dart';
import 'contacts_event.dart';
import 'contacts_state.dart';

class ContactsBloc extends Bloc<ContactsEvent, ContactsState> {
  final ContactsRepository _contactsRepository;

  ContactsBloc({ContactsRepository? contactsRepository})
      : _contactsRepository = contactsRepository ?? ContactsRepository(),
        super(ContactsInitial()) {
    on<FetchContacts>(_onFetchContacts);
    on<AddContact>(_onAddContact);
    on<RemoveContact>(_onRemoveContact);
  }

  Future<void> _onFetchContacts(FetchContacts event, Emitter<ContactsState> emit) async {
    emit(ContactsLoading());
    try {
      final contacts = await _contactsRepository.getContacts();
      emit(ContactsLoaded(contacts: contacts));
    } catch (e) {
      emit(ContactsError(message: e.toString()));
    }
  }

  Future<void> _onAddContact(AddContact event, Emitter<ContactsState> emit) async {
    try {
      await _contactsRepository.createContact(ContactCreateRequest(
        name: event.name,
        upiId: event.upiId,
        phone: event.phone,
      ));
      add(FetchContacts());
    } catch (e) {
      emit(ContactsError(message: e.toString()));
    }
  }

  Future<void> _onRemoveContact(RemoveContact event, Emitter<ContactsState> emit) async {
    try {
      await _contactsRepository.deleteContact(event.contactId);
      add(FetchContacts());
    } catch (e) {
      emit(ContactsError(message: e.toString()));
    }
  }
}
