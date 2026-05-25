import '../../../../core/network/api_client.dart';
import '../dto/app_user_dto.dart';
import '../dto/auth_tokens_dto.dart';

class AuthRemoteDataSource {
  AuthRemoteDataSource(this._apiClient);

  final ApiClient _apiClient;

  Future<(AuthTokensDto tokens, AppUserDto user)> login({
    required String login,
    required String password,
    String? device,
    String? platform,
  }) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      '/auth/login',
      data: {
        'login': login,
        'password': password,
        'device': device,
        'platform': platform,
      },
    );
    final data = response.data ?? <String, dynamic>{};
    return (
      AuthTokensDto.fromJson(data),
      AppUserDto.fromJson(data['user'] as Map<String, dynamic>),
    );
  }

  Future<(AuthTokensDto tokens, AppUserDto user)> register({
    required String fullName,
    required String email,
    required String password,
    required String passwordConfirmation,
  }) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      '/auth/register',
      data: {
        'full_name': fullName,
        'email': email,
        'password': password,
        'password_confirmation': passwordConfirmation,
      },
    );
    final data = response.data ?? <String, dynamic>{};
    return (
      AuthTokensDto.fromJson(data),
      AppUserDto.fromJson(data['user'] as Map<String, dynamic>),
    );
  }

  Future<AuthTokensDto> refresh({
    required String refreshToken,
  }) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      '/auth/refresh',
      data: {'refresh': refreshToken},
    );
    final data = response.data ?? <String, dynamic>{};
    return AuthTokensDto(
      access: data['access'] as String,
      refresh: refreshToken,
    );
  }

  Future<AppUserDto> getCurrentUser() async {
    final response = await _apiClient.dio.get<Map<String, dynamic>>('/me');
    return AppUserDto.fromJson(response.data ?? <String, dynamic>{});
  }

  Future<void> logout({required String refreshToken}) async {
    await _apiClient.dio.post<void>(
      '/auth/logout',
      data: {'refresh': refreshToken},
    );
  }
}
