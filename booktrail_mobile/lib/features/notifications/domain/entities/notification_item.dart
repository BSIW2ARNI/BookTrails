import 'package:equatable/equatable.dart';

class NotificationItem extends Equatable {
  const NotificationItem({
    required this.id,
    required this.title,
    required this.text,
    required this.type,
    required this.createdAt,
    required this.read,
  });

  final int id;
  final String title;
  final String text;
  final String type;
  final String createdAt;
  final bool read;

  @override
  List<Object?> get props => [id, title, text, type, createdAt, read];
}
