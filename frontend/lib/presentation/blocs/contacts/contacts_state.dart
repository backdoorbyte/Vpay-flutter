import 'package:equatable/equatable.dart';

import '../../../data/models/contact.dart';

abstract class ContactsState extends Equatable {
  @override
  List<Object?> get props => [];
}

class ContactsInitial extends ContactsState {}

class ContactsLoading extends ContactsState {}

class ContactsLoaded extends ContactsState {
  final List<Contact> contacts;

  ContactsLoaded({this.contacts = const []});

  @override
  List<Object?> get props => [contacts];
}

class ContactsError extends ContactsState {
  final String message;

  ContactsError({required this.message});

  @override
  List<Object?> get props => [message];
}
