import '../../domain/entities/app_user.dart';
import '../../domain/entities/auth_tokens.dart';
import '../../domain/repositories/auth_repository.dart';
import '../datasources/auth_remote_data_source.dart';

class AuthRepositoryImpl implements AuthRepository {
  AuthRepositoryImpl(this._remoteDataSource);

  final AuthRemoteDataSource _remoteDataSource;

  @override
  Future<(AuthTokens tokens, AppUser user)> login({
    required String login,
    required String password,
    String? device,
    String? platform,
  }) async {
    final result = await _remoteDataSource.login(
      login: login,
      password: password,
      device: device,
      platform: platform,
    );
    return (result.$1.toDomain(), result.$2.toDomain());
  }

  @override
  Future<(AuthTokens tokens, AppUser user)> register({
    required String fullName,
    required String email,
    required String password,
    required String passwordConfirmation,
  }) async {
    final result = await _remoteDataSource.register(
      fullName: fullName,
      email: email,
      password: password,
      passwordConfirmation: passwordConfirmation,
    );
    return (result.$1.toDomain(), result.$2.toDomain());
  }

  @override
  Future<AuthTokens> refresh({required String refreshToken}) async {
    final dto = await _remoteDataSource.refresh(refreshToken: refreshToken);
    return dto.toDomain();
  }

  @override
  Future<AppUser> getCurrentUser() async {
    final dto = await _remoteDataSource.getCurrentUser();
    return dto.toDomain();
  }

  @override
  Future<void> logout({required String refreshToken}) {
    return _remoteDataSource.logout(refreshToken: refreshToken);
  }
}
