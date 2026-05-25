import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/widgets/async_value_view.dart';
import '../../application/recommendations_provider.dart';
import '../../domain/entities/recommendation_item.dart';

class RecommendationsPage extends ConsumerWidget {
  const RecommendationsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recommendations = ref.watch(recommendationsProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Для вас')),
      body: AsyncValueView<List<RecommendationItem>>(
        value: recommendations,
        onRetry: () => ref.invalidate(recommendationsProvider),
        data: (items) {
          if (items.isEmpty) {
            return const Center(child: Text('Рекомендаций пока нет.'));
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: items.length,
            separatorBuilder: (_, __) => const SizedBox(height: 12),
            itemBuilder: (context, index) {
              final item = items[index];
              return Card(
                child: ListTile(
                  title: Text(item.title),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const SizedBox(height: 6),
                      Text(item.authors.join(', ')),
                      const SizedBox(height: 6),
                      Text(item.explanation),
                    ],
                  ),
                  trailing: Text(item.score.toStringAsFixed(2)),
                  onTap: () => context.push('/books/${item.bookId}'),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
