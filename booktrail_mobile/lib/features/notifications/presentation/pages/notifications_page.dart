import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/widgets/async_value_view.dart';
import '../../application/notifications_provider.dart';
import '../../domain/entities/notification_item.dart';

class NotificationsPage extends ConsumerWidget {
  const NotificationsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifications = ref.watch(notificationsProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Уведомления'),
        actions: [
          TextButton(
            onPressed: () async {
              await ref.read(notificationActionsProvider).markAllRead();
            },
            child: const Text('Прочитать все'),
          ),
        ],
      ),
      body: AsyncValueView<List<NotificationItem>>(
        value: notifications,
        onRetry: () => ref.invalidate(notificationsProvider),
        data: (items) {
          if (items.isEmpty) {
            return const Center(child: Text('Уведомлений пока нет.'));
          }

          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: items.length,
            separatorBuilder: (_, __) => const SizedBox(height: 12),
            itemBuilder: (context, index) {
              final item = items[index];
              return Card(
                child: ListTile(
                  onTap: item.read
                      ? null
                      : () async {
                          await ref.read(notificationActionsProvider).markRead(item.id);
                        },
                  title: Text(item.title.isEmpty ? item.type : item.title),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const SizedBox(height: 6),
                      Text(item.text),
                      const SizedBox(height: 6),
                      Text(item.createdAt),
                    ],
                  ),
                  trailing: Icon(
                    item.read ? Icons.mark_email_read_outlined : Icons.mark_email_unread_outlined,
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
