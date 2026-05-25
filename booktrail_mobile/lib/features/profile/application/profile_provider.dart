import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers/core_providers.dart';
import '../domain/entities/profile_details.dart';

final profileActionsProvider = Provider<ProfileActions>((ref) {
  return ProfileActions(ref);
});

final profileProvider = FutureProvider<ProfileDetails>((ref) async {
  final response = await ref.watch(apiClientProvider).dio.get<Map<String, dynamic>>('/me');
  final data = response.data ?? <String, dynamic>{};
  final stats = data['stats'] as Map<String, dynamic>? ?? const {};
  final sessions = data['sessions'] as List<dynamic>? ?? const [];
  return ProfileDetails(
    displayName: (data['display_name'] ?? '') as String,
    email: (data['email'] ?? '') as String,
    avatar: (data['avatar'] ?? '') as String,
    status: (data['status'] ?? '') as String,
    stats: ProfileStats(
      trackedBooks: (stats['tracked_books'] ?? 0) as int,
      reviews: (stats['reviews'] ?? 0) as int,
      eventsLogged: (stats['events_logged'] ?? 0) as int,
      recommendationMatch: (stats['recommendation_match'] ?? '0%') as String,
    ),
    sessions: sessions
        .map(
          (item) => ProfileSession(
            device: (item['device'] ?? '') as String,
            location: (item['location'] ?? '') as String,
            lastSeen: (item['last_seen'] ?? '') as String,
            current: item['current'] as bool,
          ),
        )
        .toList(),
  );
});

class ProfileActions {
  ProfileActions(this._ref);

  final Ref _ref;

  Future<void> updateProfile({
    required String fullName,
    required String email,
    required String avatar,
    required String status,
  }) async {
    await _ref.read(apiClientProvider).dio.patch<void>(
      '/me',
      data: {
        'full_name': fullName,
        'email': email,
        'avatar': avatar,
        'status': status,
        'privacy': {
          'show_profile': true,
          'share_reviews': true,
          'nfc_visibility': false,
        },
      },
    );
    _ref.invalidate(profileProvider);
  }
}
