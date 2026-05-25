import 'package:equatable/equatable.dart';

class AppUser extends Equatable {
  const AppUser({
    required this.id,
    required this.email,
    required this.displayName,
    required this.isAdmin,
  });

  final int id;
  final String email;
  final String displayName;
  final bool isAdmin;

  @override
  List<Object?> get props => [id, email, displayName, isAdmin];
}
