import '../../domain/entities/app_user.dart';

class AppUserDto {
  const AppUserDto({
    required this.id,
    required this.email,
    required this.displayName,
    required this.isAdmin,
  });

  factory AppUserDto.fromJson(Map<String, dynamic> json) {
    return AppUserDto(
      id: json['id'] as int,
      email: json['email'] as String,
      displayName: (json['display_name'] ?? json['displayName'] ?? '') as String,
      isAdmin: (json['is_admin'] ?? false) as bool,
    );
  }

  final int id;
  final String email;
  final String displayName;
  final bool isAdmin;

  AppUser toDomain() {
    return AppUser(
      id: id,
      email: email,
      displayName: displayName,
      isAdmin: isAdmin,
    );
  }
}
