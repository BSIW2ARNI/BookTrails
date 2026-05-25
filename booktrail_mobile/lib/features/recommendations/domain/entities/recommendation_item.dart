import 'package:equatable/equatable.dart';

class RecommendationItem extends Equatable {
  const RecommendationItem({
    required this.bookId,
    required this.title,
    required this.authors,
    required this.explanation,
    required this.score,
  });

  final int bookId;
  final String title;
  final List<String> authors;
  final String explanation;
  final double score;

  @override
  List<Object?> get props => [bookId, title, authors, explanation, score];
}
