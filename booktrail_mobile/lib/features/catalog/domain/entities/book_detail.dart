import 'package:equatable/equatable.dart';

class BookDetail extends Equatable {
  const BookDetail({
    required this.id,
    required this.title,
    required this.authors,
    required this.description,
    required this.year,
    required this.rating,
    required this.reviews,
    required this.copies,
  });

  final int id;
  final String title;
  final List<String> authors;
  final String description;
  final int? year;
  final double rating;
  final List<BookReview> reviews;
  final List<BookCopy> copies;

  @override
  List<Object?> get props => [id, title, authors, description, year, rating, reviews, copies];
}

class BookReview extends Equatable {
  const BookReview({
    required this.id,
    required this.author,
    required this.createdAt,
    required this.rating,
    required this.text,
    required this.isOwner,
  });

  final int id;
  final String author;
  final String createdAt;
  final int rating;
  final String text;
  final bool isOwner;

  @override
  List<Object?> get props => [id, author, createdAt, rating, text, isOwner];
}

class BookCopy extends Equatable {
  const BookCopy({
    required this.id,
    required this.code,
    required this.statusTitle,
  });

  final int id;
  final String code;
  final String statusTitle;

  @override
  List<Object?> get props => [id, code, statusTitle];
}
