import '../entities/app_user.dart';
import '../entities/auth_tokens.dart';

abstract class AuthRepository {
  Future<(AuthTokens tokens, AppUser user)> login({
    required String login,
    required String password,
    String? device,
    String? platform,
  });

  Future<(AuthTokens tokens, AppUser user)> register({
    required String fullName,
    required String email,
    required String password,
    required String passwordConfirmation,
  });

  Future<AuthTokens> refresh({required String refreshToken});

  Future<AppUser> getCurrentUser();

  Future<void> logout({required String refreshToken});
}
