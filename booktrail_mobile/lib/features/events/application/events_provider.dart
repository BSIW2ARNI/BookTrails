import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers/core_providers.dart';
import '../domain/entities/event_item.dart';

final eventsProvider = FutureProvider<List<EventItem>>((ref) async {
  final response = await ref.watch(apiClientProvider).dio.get<Map<String, dynamic>>('/events');
  final items = response.data?['items'] as List<dynamic>? ?? const [];
  return items
      .map(
        (item) => EventItem(
          id: item['id'] as int,
          eventTitle: (item['event_type'] as Map<String, dynamic>)['title'] as String,
          dateTime: item['date_time'] as String,
          placeText: (item['place_text'] ?? '') as String,
          text: (item['text'] ?? '') as String,
          bookTitle: item['book_title'] as String,
        ),
      )
      .toList();
});
