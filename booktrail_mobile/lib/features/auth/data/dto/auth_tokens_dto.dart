import '../../domain/entities/auth_tokens.dart';

class AuthTokensDto {
  const AuthTokensDto({
    required this.access,
    required this.refresh,
  });

  factory AuthTokensDto.fromJson(Map<String, dynamic> json) {
    return AuthTokensDto(
      access: json['access'] as String,
      refresh: json['refresh'] as String,
    );
  }

  final String access;
  final String refresh;

  AuthTokens toDomain() {
    return AuthTokens(access: access, refresh: refresh);
  }
}
