import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import '../../../core/providers/core_providers.dart';
import '../domain/entities/book_detail.dart';
import '../domain/entities/book_summary.dart';
import '../domain/entities/copy_detail.dart';

final catalogRepositoryProvider = Provider<CatalogRepository>((ref) {
  return CatalogRepository(ref.watch(apiClientProvider));
});

class CatalogRepository {
  CatalogRepository(this._apiClient);

  final ApiClient _apiClient;

  Future<List<BookSummary>> fetchBooks({String query = ''}) async {
    final response = await _apiClient.dio.get<Map<String, dynamic>>(
      '/books',
      queryParameters: query.isEmpty ? null : {'q': query},
    );
    final items = (response.data?['items'] as List<dynamic>? ?? []);
    return items
        .map(
          (item) => BookSummary(
            id: item['id'] as int,
            title: item['title'] as String,
            authors: List<String>.from(item['authors'] as List<dynamic>? ?? const []),
            description: (item['description'] ?? '') as String,
            accent: (item['accent'] ?? 'blue') as String,
            rating: ((item['rating'] ?? 0.0) as num).toDouble(),
            reviewsCount: (item['reviews_count'] ?? 0) as int,
          ),
        )
        .toList();
  }

  Future<BookDetail> fetchBookDetail(int id) async {
    final response = await _apiClient.dio.get<Map<String, dynamic>>('/books/$id');
    final data = response.data ?? <String, dynamic>{};
    return BookDetail(
      id: data['id'] as int,
      title: data['title'] as String,
      authors: List<String>.from(data['authors'] as List<dynamic>? ?? const []),
      description: (data['description'] ?? '') as String,
      year: data['year'] as int?,
      rating: ((data['rating'] ?? 0.0) as num).toDouble(),
      reviews: (data['reviews'] as List<dynamic>? ?? const [])
          .map(
            (item) => BookReview(
              id: item['id'] as int,
              author: item['author'] as String,
              createdAt: item['created_at'] as String,
              rating: item['rating'] as int,
              text: (item['text'] ?? '') as String,
              isOwner: (item['is_owner'] ?? false) as bool,
            ),
          )
          .toList(),
      copies: (data['copies'] as List<dynamic>? ?? const [])
          .map(
            (item) => BookCopy(
              id: item['id'] as int,
              code: item['code'] as String,
              statusTitle: (item['status'] as Map<String, dynamic>)['title'] as String,
            ),
          )
          .toList(),
    );
  }

  Future<CopyDetail> fetchCopyDetail(int id) async {
    final response = await _apiClient.dio.get<Map<String, dynamic>>('/copies/$id');
    final data = response.data ?? <String, dynamic>{};
    final status = data['status'] as Map<String, dynamic>;
    final presence = data['presence'] as Map<String, dynamic>? ?? const <String, dynamic>{};
    final holder = presence['holder'] as Map<String, dynamic>?;
    final activeBind = data['active_bind'] as Map<String, dynamic>?;
    return CopyDetail(
      id: data['id'] as int,
      code: data['code'] as String,
      bookTitle: (data['book'] as Map<String, dynamic>)['title'] as String,
      statusCode: status['code'] as String,
      statusTitle: status['title'] as String,
      activeTagUid: activeBind?['tag_uid'] as String?,
      holderDisplayName: holder?['display_name'] as String?,
      isHeldByCurrentUser: (presence['held_by_current_user'] ?? false) as bool,
      canUpdateStatus: ((data['permissions'] as Map<String, dynamic>? ?? const <String, dynamic>{})['can_update_status'] ?? false) as bool,
      availableStatuses: (data['available_statuses'] as List<dynamic>? ?? const [])
          .map(
            (item) => CopyStatusOption(
              code: (item as Map<String, dynamic>)['code'] as String,
              title: item['title'] as String,
            ),
          )
          .toList(),
      moves: (data['moves'] as List<dynamic>? ?? const [])
          .map(
            (item) => CopyMove(
              eventTitle: (item['event_type'] as Map<String, dynamic>)['title'] as String,
              dateTime: item['date_time'] as String,
              placeText: (item['place_text'] ?? '') as String,
              text: (item['text'] ?? '') as String,
            ),
          )
          .toList(),
    );
  }

  Future<void> saveReview({
    required int bookId,
    int? reviewId,
    required int rating,
    required String text,
  }) async {
    final payload = {
      'rating': rating,
      'text': text,
    };
    if (reviewId == null) {
      await _apiClient.dio.post<void>('/books/$bookId/reviews', data: payload);
      return;
    }
    await _apiClient.dio.patch<void>('/reviews/$reviewId', data: payload);
  }

  Future<void> deleteReview({required int reviewId}) async {
    await _apiClient.dio.delete<void>('/reviews/$reviewId');
  }

  Future<void> createMove({
    required int copyId,
    required String eventTypeCode,
    required String placeText,
    required String text,
  }) async {
    await _apiClient.dio.post<void>(
      '/copies/$copyId/moves',
      data: {
        'event_type_code': eventTypeCode,
        'place_text': placeText,
        'text': text,
      },
    );
  }

  Future<void> updateCopyStatus({
    required int copyId,
    required String statusCode,
    String note = '',
  }) async {
    await _apiClient.dio.patch<void>(
      '/copies/$copyId',
      data: {
        'status_code': statusCode,
        'note': note,
      },
    );
  }

  Future<void> bindTag({
    required int copyId,
    required String tagUid,
  }) async {
    await _apiClient.dio.post<void>(
      '/copies/$copyId/bind-tag',
      data: {'tag_uid': tagUid},
    );
  }

  Future<void> unbindTag({required int copyId}) async {
    await _apiClient.dio.post<void>(
      '/copies/$copyId/unbind-tag',
      data: const {},
    );
  }
}
