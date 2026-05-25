import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/widgets/async_value_view.dart';
import '../../application/catalog_providers.dart';
import '../../data/catalog_repository.dart';
import '../../domain/entities/book_detail.dart';

class BookDetailPage extends ConsumerWidget {
  const BookDetailPage({required this.bookId, super.key});

  final int bookId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final detail = ref.watch(bookDetailProvider(bookId));
    return Scaffold(
      appBar: AppBar(title: const Text('Книга')),
      body: AsyncValueView<BookDetail>(
        value: detail,
        onRetry: () => ref.invalidate(bookDetailProvider(bookId)),
        data: (book) {
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text(book.title, style: Theme.of(context).textTheme.headlineMedium),
              const SizedBox(height: 8),
              Text(book.authors.join(', '), style: Theme.of(context).textTheme.bodyLarge),
              if (book.year != null) ...[
                const SizedBox(height: 8),
                Text('Год: ${book.year}'),
              ],
              const SizedBox(height: 12),
              Text(book.description.isEmpty ? 'Описание пока не заполнено.' : book.description),
              const SizedBox(height: 16),
              Text('Рейтинг: ${book.rating.toStringAsFixed(1)}', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 20),
              Text('Экземпляры', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              for (final copy in book.copies)
                Card(
                  child: ListTile(
                    title: Text(copy.code),
                    subtitle: Text(copy.statusTitle),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () => context.push('/copies/${copy.id}'),
                  ),
                ),
              const SizedBox(height: 20),
              Text('Отзывы', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              ElevatedButton(
                onPressed: () => _showReviewSheet(context, ref, book),
                child: const Text('Мой отзыв'),
              ),
              const SizedBox(height: 8),
              if (book.reviews.isEmpty) const Text('Отзывов пока нет.'),
              for (final review in book.reviews)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('${review.author} • ${review.rating}/5'),
                        const SizedBox(height: 6),
                        Text(review.createdAt),
                        const SizedBox(height: 10),
                        Text(review.text),
                        if (review.isOwner) ...[
                          const SizedBox(height: 12),
                          Row(
                            children: [
                              TextButton(
                                onPressed: () => _showReviewSheet(context, ref, book, review: review),
                                child: const Text('Изменить'),
                              ),
                              TextButton(
                                onPressed: () async {
                                  await ref.read(catalogRepositoryProvider).deleteReview(reviewId: review.id);
                                  ref.invalidate(bookDetailProvider(bookId));
                                },
                                child: const Text('Удалить'),
                              ),
                            ],
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }

  Future<void> _showReviewSheet(
    BuildContext context,
    WidgetRef ref,
    BookDetail book,
    {BookReview? review}
  ) async {
    final ratingController = TextEditingController(text: (review?.rating ?? 5).toString());
    final textController = TextEditingController(text: review?.text ?? '');
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (context) {
        return Padding(
          padding: EdgeInsets.fromLTRB(
            16,
            16,
            16,
            16 + MediaQuery.of(context).viewInsets.bottom,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: ratingController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Оценка 1-5'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: textController,
                minLines: 3,
                maxLines: 5,
                decoration: const InputDecoration(labelText: 'Отзыв'),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () async {
                  await ref.read(catalogRepositoryProvider).saveReview(
                        bookId: book.id,
                        reviewId: review?.id,
                        rating: int.tryParse(ratingController.text.trim()) ?? 5,
                        text: textController.text.trim(),
                      );
                  ref.invalidate(bookDetailProvider(bookId));
                  if (context.mounted) {
                    Navigator.of(context).pop();
                  }
                },
                child: const Text('Сохранить отзыв'),
              ),
            ],
          ),
        );
      },
    );
  }
}
