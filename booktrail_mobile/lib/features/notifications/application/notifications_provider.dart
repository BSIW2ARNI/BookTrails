import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers/core_providers.dart';
import '../domain/entities/notification_item.dart';

final notificationActionsProvider = Provider<NotificationActions>((ref) {
  return NotificationActions(ref);
});

final notificationsProvider = FutureProvider<List<NotificationItem>>((ref) async {
  final response = await ref.watch(apiClientProvider).dio.get<Map<String, dynamic>>('/notifications');
  final items = response.data?['items'] as List<dynamic>? ?? const [];
  return items
      .map(
        (item) => NotificationItem(
          id: item['id'] as int,
          title: (item['title'] ?? '') as String,
          text: (item['text'] ?? '') as String,
          type: (item['type'] ?? '') as String,
          createdAt: item['created_at'] as String,
          read: item['read'] as bool,
        ),
      )
      .toList();
});

class NotificationActions {
  NotificationActions(this._ref);

  final Ref _ref;

  Future<void> markRead(int id) async {
    await _ref.read(apiClientProvider).dio.post<void>('/notifications/$id/mark-read', data: const {});
    _ref.invalidate(notificationsProvider);
  }

  Future<void> markAllRead() async {
    await _ref.read(apiClientProvider).dio.post<void>('/notifications/mark-all-read', data: const {});
    _ref.invalidate(notificationsProvider);
  }
}
