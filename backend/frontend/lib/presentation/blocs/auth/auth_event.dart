import 'package:equatable/equatable.dart';

abstract class AuthEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class AuthCheckRequested extends AuthEvent {}

class AuthSignedIn extends AuthEvent {
  final String email;
  final String password;

  AuthSignedIn({required this.email, required this.password});

  @override
  List<Object?> get props => [email, password];
}

class AuthSignedUp extends AuthEvent {
  final String email;
  final String password;

  AuthSignedUp({required this.email, required this.password});

  @override
  List<Object?> get props => [email, password];
}

class AuthSignedOut extends AuthEvent {}
