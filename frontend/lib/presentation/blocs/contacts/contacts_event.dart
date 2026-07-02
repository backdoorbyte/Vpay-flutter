import 'package:equatable/equatable.dart';

abstract class ContactsEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class FetchContacts extends ContactsEvent {}

class AddContact extends ContactsEvent {
  final String name;
  final String upiId;
  final String? phone;

  AddContact({required this.name, required this.upiId, this.phone});

  @override
  List<Object?> get props => [name, upiId, phone];
}

class RemoveContact extends ContactsEvent {
  final int contactId;

  RemoveContact({required this.contactId});

  @override
  List<Object?> get props => [contactId];
}
