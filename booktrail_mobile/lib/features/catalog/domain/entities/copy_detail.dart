import 'package:equatable/equatable.dart';

class CopyDetail extends Equatable {
  const CopyDetail({
    required this.id,
    required this.code,
    required this.bookTitle,
    required this.statusCode,
    required this.statusTitle,
    required this.activeTagUid,
    required this.holderDisplayName,
    required this.isHeldByCurrentUser,
    required this.canUpdateStatus,
    required this.availableStatuses,
    required this.moves,
  });

  final int id;
  final String code;
  final String bookTitle;
  final String statusCode;
  final String statusTitle;
  final String? activeTagUid;
  final String? holderDisplayName;
  final bool isHeldByCurrentUser;
  final bool canUpdateStatus;
  final List<CopyStatusOption> availableStatuses;
  final List<CopyMove> moves;

  @override
  List<Object?> get props => [id, code, bookTitle, statusCode, statusTitle, activeTagUid, holderDisplayName, isHeldByCurrentUser, canUpdateStatus, availableStatuses, moves];
}

class CopyStatusOption extends Equatable {
  const CopyStatusOption({
    required this.code,
    required this.title,
  });

  final String code;
  final String title;

  @override
  List<Object?> get props => [code, title];
}

class CopyMove extends Equatable {
  const CopyMove({
    required this.eventTitle,
    required this.dateTime,
    required this.placeText,
    required this.text,
  });

  final String eventTitle;
  final String dateTime;
  final String placeText;
  final String text;

  @override
  List<Object?> get props => [eventTitle, dateTime, placeText, text];
}
