import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/widgets/async_value_view.dart';
import '../../application/events_provider.dart';
import '../../domain/entities/event_item.dart';

class EventsPage extends ConsumerWidget {
  const EventsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final events = ref.watch(eventsProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('События')),
      body: AsyncValueView<List<EventItem>>(
        value: events,
        onRetry: () => ref.invalidate(eventsProvider),
        data: (items) {
          if (items.isEmpty) {
            return const Center(child: Text('Событий пока нет.'));
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: items.length,
            separatorBuilder: (_, __) => const SizedBox(height: 12),
            itemBuilder: (context, index) {
              final event = items[index];
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(event.eventTitle, style: Theme.of(context).textTheme.titleLarge),
                      const SizedBox(height: 6),
                      Text(event.bookTitle),
                      const SizedBox(height: 6),
                      Text(event.dateTime),
                      if (event.placeText.isNotEmpty) ...[
                        const SizedBox(height: 8),
                        Text(event.placeText),
                      ],
                      if (event.text.isNotEmpty) ...[
                        const SizedBox(height: 10),
                        Text(event.text),
                      ],
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
