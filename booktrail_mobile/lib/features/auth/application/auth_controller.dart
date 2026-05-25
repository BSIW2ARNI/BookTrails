import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/app_exception.dart';
import '../../../core/providers/core_providers.dart';
import '../../../core/storage/token_storage.dart';
import '../data/datasources/auth_remote_data_source.dart';
import '../data/repositories/auth_repository_impl.dart';
import '../domain/entities/auth_session_state.dart';
import '../domain/repositories/auth_repository.dart';

final authRemoteDataSourceProvider = Provider<AuthRemoteDataSource>((ref) {
  return AuthRemoteDataSource(ref.watch(apiClientProvider));
});

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepositoryImpl(ref.watch(authRemoteDataSourceProvider));
});

final authControllerProvider =
    AsyncNotifierProvider<AuthController, AuthSessionState>(AuthController.new);

class AuthController extends AsyncNotifier<AuthSessionState> {
  AuthRepository get _repository => ref.read(authRepositoryProvider);
  TokenStorage get _tokenStorage => ref.read(tokenStorageProvider);

  @override
  Future<AuthSessionState> build() async {
    return restoreSession();
  }

  Future<AuthSessionState> restoreSession() async {
    final access = await _tokenStorage.readAccessToken();
    final refresh = await _tokenStorage.readRefreshToken();

    if (access == null || access.isEmpty || refresh == null || refresh.isEmpty) {
      return const AuthSessionState.unauthenticated();
    }

    try {
      final user = await _repository.getCurrentUser();
      return AuthSessionState.authenticated(user);
    } on DioException {
      try {
        final tokens = await _repository.refresh(refreshToken: refresh);
        await _tokenStorage.saveTokens(
          accessToken: tokens.access,
          refreshToken: tokens.refresh,
        );
        final user = await _repository.getCurrentUser();
        return AuthSessionState.authenticated(user);
      } catch (_) {
        await _tokenStorage.clear();
        return const AuthSessionState.unauthenticated();
      }
    } catch (_) {
      await _tokenStorage.clear();
      return const AuthSessionState.unauthenticated();
    }
  }

  Future<void> login({
    required String login,
    required String password,
  }) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      try {
        final result = await _repository.login(
          login: login,
          password: password,
          platform: 'flutter',
        );
        await _tokenStorage.saveTokens(
          accessToken: result.$1.access,
          refreshToken: result.$1.refresh,
        );
        return AuthSessionState.authenticated(result.$2);
      } on DioException catch (error) {
        throw _mapDioException(error);
      }
    });
  }

  Future<void> register({
    required String fullName,
    required String email,
    required String password,
    required String passwordConfirmation,
  }) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      try {
        final result = await _repository.register(
          fullName: fullName,
          email: email,
          password: password,
          passwordConfirmation: passwordConfirmation,
        );
        await _tokenStorage.saveTokens(
          accessToken: result.$1.access,
          refreshToken: result.$1.refresh,
        );
        return AuthSessionState.authenticated(result.$2);
      } on DioException catch (error) {
        throw _mapDioException(error);
      }
    });
  }

  Future<void> logout() async {
    final refreshToken = await _tokenStorage.readRefreshToken();
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      if (refreshToken != null && refreshToken.isNotEmpty) {
        try {
          await _repository.logout(refreshToken: refreshToken);
        } catch (_) {
          // Local logout should still complete even if backend request fails.
        }
      }
      await _tokenStorage.clear();
      return const AuthSessionState.unauthenticated();
    });
  }

  AppException _mapDioException(DioException error) {
    final data = error.response?.data;
    if (data is Map<String, dynamic>) {
      final errorBody = data['error'];
      if (errorBody is Map<String, dynamic>) {
        return AppException(
          (errorBody['message'] ?? 'Ошибка запроса.') as String,
          code: errorBody['code'] as String?,
          details: errorBody['details'] is Map<String, dynamic>
              ? errorBody['details'] as Map<String, dynamic>
              : null,
        );
      }
    }
    return const AppException('Не удалось выполнить запрос к серверу.');
  }
}
