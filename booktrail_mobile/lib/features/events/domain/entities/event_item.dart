import 'package:equatable/equatable.dart';

class EventItem extends Equatable {
  const EventItem({
    required this.id,
    required this.eventTitle,
    required this.dateTime,
    required this.placeText,
    required this.text,
    required this.bookTitle,
  });

  final int id;
  final String eventTitle;
  final String dateTime;
  final String placeText;
  final String text;
  final String bookTitle;

  @override
  List<Object?> get props => [id, eventTitle, dateTime, placeText, text, bookTitle];
}
