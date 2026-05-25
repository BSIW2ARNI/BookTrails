import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/catalog_repository.dart';
import '../domain/entities/book_detail.dart';
import '../domain/entities/book_summary.dart';
import '../domain/entities/copy_detail.dart';

final catalogQueryProvider = StateProvider<String>((ref) => '');

final booksProvider = FutureProvider<List<BookSummary>>((ref) {
  final query = ref.watch(catalogQueryProvider);
  return ref.watch(catalogRepositoryProvider).fetchBooks(query: query);
});

final bookDetailProvider = FutureProvider.family<BookDetail, int>((ref, id) {
  return ref.watch(catalogRepositoryProvider).fetchBookDetail(id);
});

final copyDetailProvider = FutureProvider.family<CopyDetail, int>((ref, id) {
  return ref.watch(catalogRepositoryProvider).fetchCopyDetail(id);
});
