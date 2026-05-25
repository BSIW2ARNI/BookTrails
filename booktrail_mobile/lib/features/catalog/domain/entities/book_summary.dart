import 'package:equatable/equatable.dart';

class BookSummary extends Equatable {
  const BookSummary({
    required this.id,
    required this.title,
    required this.authors,
    required this.description,
    required this.accent,
    required this.rating,
    required this.reviewsCount,
  });

  final int id;
  final String title;
  final List<String> authors;
  final String description;
  final String accent;
  final double rating;
  final int reviewsCount;

  @override
  List<Object?> get props => [id, title, authors, description, accent, rating, reviewsCount];
}
