import 'package:equatable/equatable.dart';

class AuthTokens extends Equatable {
  const AuthTokens({
    required this.access,
    required this.refresh,
  });

  final String access;
  final String refresh;

  @override
  List<Object?> get props => [access, refresh];
}
