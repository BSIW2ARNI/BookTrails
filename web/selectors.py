from __future__ import annotations

from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Prefetch, Q, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import AuthSession, Author, Book, Copy, Move, Notification, Recommendation, Review, TagBind


def _fmt_dt(dt) -> str:
    if not dt:
        return ''
    return timezone.localtime(dt).strftime('%d.%m.%Y %H:%M')


def _prefetched_authors():
    return Prefetch('authors', queryset=Author.objects.order_by('book_authors__sort_order', 'name'), to_attr='prefetched_authors')


def _user_display_name(user: User | None) -> str:
    if not user:
        return 'Аноним'
    profile = getattr(user, 'booktrail_profile', None)
    if profile:
        return profile.display_name
    full_name = user.get_full_name().strip()
    return full_name or user.username


def move_to_event_dict(move: Move) -> dict:
    return {
        'type': move.get_event_type_display(),
        'event_type': move.get_event_type_display(),
        'time': _fmt_dt(move.date_time),
        'date_time': _fmt_dt(move.date_time),
        'place': move.place_text,
        'place_text': move.place_text,
        'comment': move.text,
        'text': move.text,
        'source': move.source,
        'payload': move.payload,
        'copy_id': move.copy_id,
        'book_id': move.copy.book_id,
        'book_title': move.copy.book.title,
    }


def get_latest_events(limit: int = 12) -> list[dict]:
    latest_moves = (
        Move.objects.select_related('copy', 'copy__book', 'user')
        .prefetch_related('user__booktrail_profile')
        .order_by('-date_time')[:limit]
    )
    return [move_to_event_dict(move) for move in latest_moves]


def get_catalog_data(query: str, genre: str, language: str) -> dict:
    qs = Book.objects.select_related('genre', 'language').prefetch_related(_prefetched_authors())
    if query:
        qs = qs.filter(
            Q(title__icontains=query)
            | Q(authors__name__icontains=query)
            | Q(isbn__icontains=query)
        ).distinct()
    if genre:
        qs = qs.filter(genre__slug=genre)
    if language:
        qs = qs.filter(language__code=language)

    qs = qs.annotate(
        rating=Coalesce(Avg('reviews__rating'), Value(0.0)),
        reviews_count=Count('reviews', distinct=True),
    ).order_by('title')

    genres = list(Book.objects.exclude(genre__isnull=True).values_list('genre__name', 'genre__slug').distinct().order_by('genre__name'))
    languages = list(Book.objects.exclude(language__isnull=True).values_list('language__name', 'language__code').distinct().order_by('language__name'))
    return {
        'books': list(qs),
        'genres': genres,
        'languages': languages,
        'query': query,
        'selected_genre': genre or '',
        'selected_language': language or '',
    }


def get_book_for_detail(book_id: int) -> Book | None:
    return (
        Book.objects.select_related('genre', 'language')
        .prefetch_related(_prefetched_authors())
        .annotate(rating=Coalesce(Avg('reviews__rating'), Value(0.0)))
        .filter(id=book_id)
        .first()
    )


def get_user_review_for_book(book: Book, user: User) -> Review | None:
    return Review.objects.filter(book=book, author=user).first()


def get_book_reviews(book: Book, current_user: User | None) -> list[dict]:
    reviews_qs = (
        Review.objects.filter(book=book)
        .select_related('author', 'author__booktrail_profile')
        .order_by('-created_at')
    )
    current_user_id = current_user.id if current_user and current_user.is_authenticated else None
    return [
        {
            'author': _user_display_name(review.author),
            'created_at': _fmt_dt(review.created_at),
            'rating': review.rating,
            'moderation_status': review.get_moderation_status_display(),
            'text': review.text,
            'id': review.id,
            'is_owner': current_user_id is not None and review.author_id == current_user_id,
        }
        for review in reviews_qs
    ]


def get_book_copies(book: Book) -> list[Copy]:
    copies_qs = (
        Copy.objects.filter(book=book)
        .select_related('initiator')
        .prefetch_related(
            Prefetch(
                'moves',
                queryset=Move.objects.select_related('user').order_by('-date_time'),
                to_attr='moves_all',
            )
        )
        .order_by('-created_at')
    )
    return list(copies_qs)


def get_related_books(book: Book) -> list[dict]:
    related_books_qs = (
        Book.objects.select_related('genre', 'language')
        .prefetch_related(_prefetched_authors())
        .filter(genre=book.genre)
        .exclude(id=book.id)[:6]
    )
    return [
        {
            'id': related.id,
            'book_id': related.id,
            'title': related.title,
            'authors': related.author_names,
            'accent': related.accent,
            'score': float(getattr(related, 'rating', 0.9) or 0.9),
            'explanation': 'Похоже по жанру и контексту маршрутов.',
        }
        for related in related_books_qs
    ]


def get_copy_for_detail(copy_id: int) -> Copy | None:
    return (
        Copy.objects.select_related('book', 'book__genre', 'book__language', 'initiator', 'holder', 'holder__booktrail_profile')
        .filter(id=copy_id)
        .first()
    )


def get_active_bind(copy: Copy) -> TagBind | None:
    return TagBind.objects.filter(copy=copy, ended_at__isnull=True).select_related('tag').first()


def get_copy_nfc_state(copy: Copy) -> tuple[TagBind | None, dict]:
    active_bind = get_active_bind(copy)
    nfc = {
        'tag_uid': active_bind.tag.uid if active_bind else None,
        'status': active_bind.tag.get_status_display() if active_bind else 'Не привязано',
    }
    return active_bind, nfc


def get_copy_movements(copy: Copy) -> list[dict]:
    moves = (
        Move.objects.filter(copy=copy)
        .select_related('user', 'nfc_tag', 'copy', 'copy__book')
        .order_by('-date_time')
    )
    return [move_to_event_dict(move) for move in moves]


def get_events_feed_data(event_type: str, page_number: str | int | None) -> dict:
    qs = Move.objects.select_related('copy__book', 'user').order_by('-date_time')
    if event_type:
        qs = qs.filter(event_type__code=event_type)

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(page_number or 1)
    events = [move_to_event_dict(move) for move in page_obj.object_list]
    return {'events': events, 'page_obj': page_obj}


def get_recommendations_for_user(user: User) -> list[dict]:
    recs_qs = (
        Recommendation.objects.filter(user=user)
        .select_related('book', 'book__genre', 'book__language')
        .prefetch_related('book__authors')
        .order_by('-score', '-created_at')
    )
    recs = list(recs_qs[:30])

    if not recs:
        from .recommendation_engine import persist_recommendations_for_user

        persist_recommendations_for_user(user, limit=10)
        recs = list(recs_qs[:30])

    return [
        {
            'id': recommendation.book_id,
            'book_id': recommendation.book_id,
            'title': recommendation.book.title,
            'authors': recommendation.book.author_names,
            'accent': recommendation.book.accent,
            'score': recommendation.score,
            'explanation': recommendation.explanation,
        }
        for recommendation in recs
    ]


def get_notifications_for_user(user: User) -> list[dict]:
    notifications_qs = Notification.objects.filter(user=user).order_by('-created_at')[:50]
    return [
        {
            'id': notification.id,
            'type': notification.get_kind_display(),
            'title': notification.title,
            'text': notification.text,
            'read': notification.is_read,
            'created_at': _fmt_dt(notification.created_at),
        }
        for notification in notifications_qs
    ]


def get_profile_dashboard(user: User, profile) -> dict:
    copies_count = Copy.objects.filter(initiator=user).count()
    moves_count = Move.objects.filter(user=user).count()
    reviews_count = Review.objects.filter(author=user).count()

    sessions_qs = AuthSession.objects.filter(user=user, revoked=False).order_by('-created_at')
    sessions = [
        {'device': session.device, 'location': session.location, 'last_seen': _fmt_dt(session.last_seen), 'current': session.current}
        for session in sessions_qs
    ]

    recent_reviews_qs = Review.objects.filter(author=user).order_by('-created_at')[:2]
    recent_reviews = [
        {
            'author': profile.display_name,
            'created_at': _fmt_dt(review.created_at),
            'rating': review.rating,
            'moderation_status': review.get_moderation_status_display(),
            'text': review.text,
        }
        for review in recent_reviews_qs
    ]

    user_ctx = {
        'email': user.email,
        'display_name': profile.display_name,
        'avatar': profile.avatar,
        'status': profile.status,
        'privacy': {
            'show_profile': profile.show_profile,
            'share_reviews': profile.share_reviews,
            'nfc_visibility': profile.nfc_visibility,
        },
        'stats': {
            'tracked_books': copies_count,
            'reviews': reviews_count,
            'events_logged': moves_count,
            'recommendation_match': '94%',
        },
        'sessions': sessions,
    }
    return {'user': user_ctx, 'recent_reviews': recent_reviews}


def get_scan_history(user: User, limit: int = 10) -> list[dict]:
    scans_qs = (
        Move.objects.filter(user=user, event_type__code='scan')
        .select_related('nfc_tag')
        .order_by('-date_time')[:limit]
    )
    return [
        {
            'date_time': _fmt_dt(scan.date_time),
            'tag_uid': scan.nfc_tag.uid if scan.nfc_tag else 'Нет метки',
            'place': scan.place_text,
        }
        for scan in scans_qs
    ]
