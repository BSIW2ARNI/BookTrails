import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/widgets/async_value_view.dart';
import '../../application/catalog_providers.dart';
import '../../domain/entities/book_summary.dart';

class CatalogPage extends ConsumerStatefulWidget {
  const CatalogPage({super.key});

  @override
  ConsumerState<CatalogPage> createState() => _CatalogPageState();
}

class _CatalogPageState extends ConsumerState<CatalogPage> {
  @override
  Widget build(BuildContext context) {
    final books = ref.watch(booksProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Каталог'),
        actions: [
          IconButton(
            onPressed: _refreshBooks,
            icon: const Icon(Icons.refresh),
            tooltip: 'Обновить',
          ),
        ],
      ),
      body: AsyncValueView<List<BookSummary>>(
        value: books,
        onRetry: _refreshBooks,
        data: (items) => RefreshIndicator(
          onRefresh: _handleRefresh,
          child: ListView.separated(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(16),
            itemCount: items.isEmpty ? 1 : items.length,
            separatorBuilder: (_, __) => const SizedBox(height: 12),
            itemBuilder: (context, index) {
              if (items.isEmpty) {
                return const Padding(
                  padding: EdgeInsets.only(top: 180),
                  child: Center(child: Text('Ничего не найдено.')),
                );
              }

              final book = items[index];
              return Card(
                child: InkWell(
                  borderRadius: BorderRadius.circular(20),
                  onTap: () => context.push('/books/${book.id}'),
                  child: Padding(
                    padding: const EdgeInsets.all(18),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(book.title, style: Theme.of(context).textTheme.titleLarge),
                        const SizedBox(height: 6),
                        Text(book.authors.join(', '), style: Theme.of(context).textTheme.bodyLarge),
                        const SizedBox(height: 10),
                        Text(
                          book.description.isEmpty
                              ? 'Описание пока не заполнено.'
                              : book.description,
                          maxLines: 3,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 12),
                        Text(
                          'Рейтинг: ${book.rating.toStringAsFixed(1)} • Отзывов: ${book.reviewsCount}',
                        ),
                      ],
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );
  }

  Future<void> _handleRefresh() async {
    _refreshBooks();
    await ref.read(booksProvider.future);
  }

  void _refreshBooks() {
    ref.invalidate(booksProvider);
  }
}
