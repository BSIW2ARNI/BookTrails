import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers/core_providers.dart';
import '../../auth/application/auth_controller.dart';
import '../domain/entities/recommendation_item.dart';

final recommendationsProvider = FutureProvider<List<RecommendationItem>>((ref) async {
  final authState = ref.watch(authControllerProvider);
  final userId = authState.valueOrNull?.user?.id;
  if (userId == null) {
    return const [];
  }

  final response = await ref.watch(apiClientProvider).dio.get<Map<String, dynamic>>('/recommendations');
  final items = response.data?['items'] as List<dynamic>? ?? const [];
  return items
      .map(
        (item) => RecommendationItem(
          bookId: item['book_id'] as int,
          title: item['title'] as String,
          authors: List<String>.from(item['authors'] as List<dynamic>? ?? const []),
          explanation: (item['explanation'] ?? '') as String,
          score: ((item['score'] ?? 0.0) as num).toDouble(),
        ),
      )
      .toList();
});
