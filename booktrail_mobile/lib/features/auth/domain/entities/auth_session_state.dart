import 'package:equatable/equatable.dart';

import 'app_user.dart';

class AuthSessionState extends Equatable {
  const AuthSessionState._({
    required this.status,
    this.user,
    this.errorMessage,
  });

  const AuthSessionState.unknown() : this._(status: AuthStatus.unknown);

  const AuthSessionState.authenticated(AppUser user)
      : this._(status: AuthStatus.authenticated, user: user);

  const AuthSessionState.unauthenticated({String? errorMessage})
      : this._(
          status: AuthStatus.unauthenticated,
          errorMessage: errorMessage,
        );

  final AuthStatus status;
  final AppUser? user;
  final String? errorMessage;

  bool get isAuthenticated => status == AuthStatus.authenticated && user != null;

  @override
  List<Object?> get props => [status, user, errorMessage];
}

enum AuthStatus {
  unknown,
  authenticated,
  unauthenticated,
}
