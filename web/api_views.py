from __future__ import annotations

from django import forms
from django.contrib.auth import authenticate, password_validation
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q
from django.db.models import Avg, Count, Value
from django.db.models.functions import Coalesce

from .api_auth import (
    authenticate_access_token,
    create_auth_session,
    refresh_access_token,
    revoke_session_by_refresh_token,
)
from .api_utils import api_error, api_success, api_view, parse_json_body
from .forms import MoveForm, NfcBindForm, ProfileForm, ReviewForm, ScanForm
from .models import Book, Copy, CopyStatus, Move, MoveEventType, Notification, Recommendation, Review
from .selectors import (
    get_active_bind,
    get_book_copies,
    get_book_for_detail,
    get_copy_for_detail,
    get_copy_movements,
    get_notifications_for_user,
    get_recommendations_for_user,
    get_related_books,
)
from .services import (
    bind_tag_to_copy,
    create_copy_move,
    create_scan_event,
    delete_book_review,
    mark_all_notifications_read,
    mark_notification_read,
    save_book_review,
    unbind_tag_from_copy,
    update_copy_status,
    update_profile,
)
from .utils import ensure_profile


def _iso(dt) -> str | None:
    return dt.isoformat().replace('+00:00', 'Z') if dt else None


def _serialize_user(user: User) -> dict:
    profile = ensure_profile(user)
    return {
        'id': user.id,
        'email': user.email,
        'display_name': profile.display_name,
        'is_admin': user.is_staff or user.is_superuser,
    }


def _serialize_book_summary(book: Book) -> dict:
    return {
        'id': book.id,
        'title': book.title,
        'authors': book.author_names,
        'genre': (
            {'name': book.genre.name, 'slug': book.genre.slug}
            if book.genre_id
            else None
        ),
        'language': (
            {'name': book.language.name, 'code': book.language.code}
            if book.language_id
            else None
        ),
        'year': book.year,
        'description': book.description,
        'cover': book.cover,
        'accent': book.accent,
        'isbn': book.isbn,
        'rating': float(getattr(book, 'rating', 0.0) or 0.0),
        'reviews_count': int(getattr(book, 'reviews_count', 0) or 0),
    }


def _serialize_review(review: Review, current_user: User | None) -> dict:
    profile = getattr(review.author, 'booktrail_profile', None) if review.author else None
    display_name = profile.display_name if profile else (review.author.get_full_name().strip() if review.author else 'Аноним')
    if review.author and not display_name:
        display_name = review.author.username
    return {
        'id': review.id,
        'author': display_name,
        'created_at': _iso(review.created_at),
        'rating': review.rating,
        'moderation_status': review.get_moderation_status_display(),
        'text': review.text,
        'is_owner': current_user is not None and review.author_id == current_user.id,
    }


def _serialize_copy_summary(copy: Copy) -> dict:
    return {
        'id': copy.id,
        'code': copy.code,
        'status': {
            'code': copy.status.code,
            'title': copy.status.title,
        },
    }


def _serialize_move(move: Move) -> dict:
    return {
        'id': move.id,
        'event_type': {
            'code': move.event_type.code,
            'title': move.event_type.title,
        },
        'date_time': _iso(move.date_time),
        'place_text': move.place_text,
        'text': move.text,
        'source': {
            'code': move.source.code,
            'title': move.source.title,
        },
        'nfc_tag_uid': move.nfc_tag.uid if move.nfc_tag_id else None,
        'copy_id': move.copy_id,
        'book_id': move.copy.book_id,
        'book_title': move.copy.book.title,
    }


def _auth_user_from_request(request):
    try:
        user, _session = authenticate_access_token(request.headers.get('Authorization'))
        return user
    except PermissionDenied:
        return None


def _require_api_user(request):
    try:
        user, _session = authenticate_access_token(request.headers.get('Authorization'))
        return user
    except PermissionDenied as error:
        return api_error('unauthorized', str(error), status=401)


def _get_copy_current_holder(copy: Copy) -> User | None:
    if copy.holder_id:
        return copy.holder
    if copy.status.code != 'with_reader':
        return None
    latest_holder_move = (
        Move.objects.filter(copy=copy, user__isnull=False)
        .select_related('user', 'user__booktrail_profile')
        .order_by('-date_time')
        .first()
    )
    return latest_holder_move.user if latest_holder_move else None


def _is_admin_user(user: User | None) -> bool:
    return bool(user and (user.is_staff or user.is_superuser))


def _form_errors(form: forms.Form) -> dict:
    return {field: [str(message) for message in messages] for field, messages in form.errors.items()}


def _serialize_copy_detail_data(copy: Copy, current_user: User | None) -> dict:
    active_bind = get_active_bind(copy)
    current_holder = _get_copy_current_holder(copy)
    moves_qs = (
        Move.objects.filter(copy=copy)
        .select_related('copy__book', 'event_type', 'source', 'nfc_tag')
        .order_by('-date_time')
    )
    return {
        'id': copy.id,
        'code': copy.code,
        'status': {
            'code': copy.status.code,
            'title': copy.status.title,
        },
        'presence': {
            'is_with_reader': copy.status.code == 'with_reader',
            'held_by_current_user': current_user is not None and current_holder is not None and current_holder.id == current_user.id,
            'holder': _serialize_user(current_holder) if current_holder else None,
        },
        'permissions': {
            'can_update_status': _is_admin_user(current_user),
        },
        'available_statuses': [
            {
                'code': status.code,
                'title': status.title,
            }
            for status in CopyStatus.objects.order_by('title')
        ],
        'book': {
            'id': copy.book_id,
            'title': copy.book.title,
        },
        'active_bind': (
            {
                'tag_uid': active_bind.tag.uid,
                'status': active_bind.tag.get_status_display(),
                'started_at': _iso(active_bind.started_at),
            }
            if active_bind
            else None
        ),
        'moves': [_serialize_move(move) for move in moves_qs],
    }


@api_view(['POST'])
def api_register(request):
    data = parse_json_body(request)

    full_name = (data.get('full_name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    password_confirmation = data.get('password_confirmation') or ''

    errors = {}
    if not full_name:
        errors['full_name'] = ['Введите имя и фамилию.']
    if not email:
        errors['email'] = ['Введите email.']
    if not password:
        errors['password'] = ['Введите пароль.']
    if password != password_confirmation:
        errors['password_confirmation'] = ['Пароли не совпадают.']
    if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists():
        errors['email'] = ['Пользователь с таким email уже существует.']

    if errors:
        return api_error('validation_error', 'Проверьте входные данные.', status=400, details=errors)

    user = User(username=email, email=email, is_active=True)
    name_parts = full_name.split(maxsplit=1)
    user.first_name = name_parts[0]
    user.last_name = name_parts[1] if len(name_parts) > 1 else ''

    try:
        password_validation.validate_password(password, user)
    except ValidationError as error:
        return api_error(
            'validation_error',
            'Проверьте входные данные.',
            status=400,
            details={'password': error.messages},
        )

    user.set_password(password)
    user.save()
    ensure_profile(user)
    access, refresh, _session = create_auth_session(user)
    return api_success({'access': access, 'refresh': refresh, 'user': _serialize_user(user)}, status=201)


@api_view(['POST'])
def api_login(request):
    data = parse_json_body(request)
    credential = (data.get('login') or '').strip()
    password = data.get('password') or ''
    device = (data.get('device') or data.get('platform') or '').strip()

    if not credential or not password:
        return api_error(
            'validation_error',
            'Проверьте входные данные.',
            status=400,
            details={'login': ['Введите логин.'], 'password': ['Введите пароль.']},
        )

    user = authenticate(request, username=credential, password=password)
    if user is None:
        user_by_email = User.objects.filter(email__iexact=credential).first()
        if user_by_email:
            user = authenticate(request, username=user_by_email.username, password=password)

    if user is None or not user.is_active:
        return api_error('invalid_credentials', 'Неверный логин/email или пароль.', status=401)

    access, refresh, _session = create_auth_session(user, device=device)
    return api_success({'access': access, 'refresh': refresh, 'user': _serialize_user(user)})


@api_view(['POST'])
def api_refresh(request):
    data = parse_json_body(request)
    refresh = data.get('refresh') or ''
    if not refresh:
        return api_error('validation_error', 'Проверьте входные данные.', status=400, details={'refresh': ['Refresh token обязателен.']})

    try:
        access, _session = refresh_access_token(refresh)
    except PermissionDenied as error:
        return api_error('invalid_refresh_token', str(error), status=401)

    return api_success({'access': access})


@api_view(['POST'])
def api_logout(request):
    data = parse_json_body(request)
    refresh = data.get('refresh') or ''
    if not refresh:
        return api_error('validation_error', 'Проверьте входные данные.', status=400, details={'refresh': ['Refresh token обязателен.']})

    try:
        revoke_session_by_refresh_token(refresh)
    except PermissionDenied as error:
        return api_error('invalid_refresh_token', str(error), status=401)

    return api_success(status=204)


@api_view(['GET', 'PATCH'])
def api_me(request):
    auth = _require_api_user(request)
    if isinstance(auth, JsonResponse):
        return auth
    user = auth

    if request.method == 'PATCH':
        profile = ensure_profile(user)
        data = parse_json_body(request)
        privacy = data.get('privacy') or {}
        form = ProfileForm(
            user=user,
            profile=profile,
            data={
                'full_name': data.get('full_name') or profile.display_name,
                'email': data.get('email') or user.email,
                'avatar': data.get('avatar') or profile.avatar,
                'status': data.get('status') or profile.status,
                'show_profile': privacy.get('show_profile', profile.show_profile),
                'share_reviews': privacy.get('share_reviews', profile.share_reviews),
                'nfc_visibility': privacy.get('nfc_visibility', profile.nfc_visibility),
            },
        )
        if not form.is_valid():
            return api_error('validation_error', 'Проверьте входные данные.', status=400, details=_form_errors(form))

        updated_profile = update_profile(form)
        return api_success(
            {
                'id': user.id,
                'email': user.email,
                'display_name': updated_profile.display_name,
                'avatar': updated_profile.avatar,
                'status': updated_profile.status,
                'privacy': {
                    'show_profile': updated_profile.show_profile,
                    'share_reviews': updated_profile.share_reviews,
                    'nfc_visibility': updated_profile.nfc_visibility,
                },
            }
        )

    profile = ensure_profile(user)
    sessions = [
        {
            'device': session.device,
            'location': session.location,
            'last_seen': _iso(session.last_seen),
            'current': session.current,
        }
        for session in user.auth_sessions.filter(revoked=False).order_by('-created_at')
    ]

    return api_success(
        {
            'id': user.id,
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
                'tracked_books': user.created_copies.count(),
                'reviews': user.reviews.count(),
                'events_logged': user.moves.count(),
                'recommendation_match': '94%',
            },
            'sessions': sessions,
        }
    )




@api_view(['GET', 'PATCH'])
def api_books(request):
    query = (request.GET.get('q') or '').strip()
    genre = (request.GET.get('genre') or '').strip()
    language = (request.GET.get('language') or '').strip()
    page_number = request.GET.get('page') or 1

    qs = Book.objects.select_related('genre', 'language').prefetch_related('authors')
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

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(page_number)

    genres = list(Book.objects.exclude(genre__isnull=True).values('genre__name', 'genre__slug').distinct().order_by('genre__name'))
    languages = list(Book.objects.exclude(language__isnull=True).values('language__name', 'language__code').distinct().order_by('language__name'))

    return api_success(
        {
            'items': [_serialize_book_summary(book) for book in page_obj.object_list],
            'filters': {
                'genres': [{'name': item['genre__name'], 'slug': item['genre__slug']} for item in genres],
                'languages': [{'name': item['language__name'], 'code': item['language__code']} for item in languages],
            },
            'pagination': {
                'page': page_obj.number,
                'page_size': paginator.per_page,
                'total': paginator.count,
            },
        }
    )


@api_view(['GET', 'PATCH'])
def api_book_detail(request, id: int):
    current_user = _auth_user_from_request(request)
    book = get_book_for_detail(id)
    if not book:
        return api_error('not_found', 'Книга не найдена.', status=404)

    reviews_qs = (
        Review.objects.filter(book=book)
        .select_related('author', 'author__booktrail_profile', 'moderation_status')
        .order_by('-created_at')
    )
    user_review = reviews_qs.filter(author=current_user).first() if current_user else None

    return api_success(
        {
            **_serialize_book_summary(book),
            'reviews': [_serialize_review(review, current_user) for review in reviews_qs],
            'copies': [_serialize_copy_summary(copy) for copy in get_book_copies(book)],
            'related_books': get_related_books(book),
            'user_review': (
                {
                    'id': user_review.id,
                    'rating': user_review.rating,
                    'text': user_review.text,
                }
                if user_review
                else None
            ),
        }
    )


@api_view(['POST'])
def api_book_review_create(request, id: int):
    auth = _require_api_user(request)
    if isinstance(auth, JsonResponse):
        return auth
    user = auth
    book = get_book_for_detail(id)
    if not book:
        return api_error('not_found', 'Книга не найдена.', status=404)

    existing = Review.objects.filter(book=book, author=user).first()
    data = parse_json_body(request)
    form = ReviewForm(data=data, instance=existing)
    if not form.is_valid():
        return api_error('validation_error', 'Проверьте входные данные.', status=400, details=_form_errors(form))

    try:
        review = save_book_review(book, user, form)
    except ValidationError as error:
        details = error.message_dict if hasattr(error, 'message_dict') else {'non_field_errors': error.messages}
        return api_error('validation_error', 'Проверьте входные данные.', status=400, details=details)

    return api_success(
        {
            'id': review.id,
            'rating': review.rating,
            'text': review.text,
            'moderation_status': review.get_moderation_status_display(),
            'created_at': _iso(review.created_at),
        },
        status=201 if existing is None else 200,
    )


@api_view(['PATCH', 'DELETE'])
def api_review_update(request, id: int):
    auth = _require_api_user(request)
    if isinstance(auth, JsonResponse):
        return auth
    user = auth
    review = Review.objects.filter(id=id, author=user).select_related('moderation_status').first()
    if not review:
        return api_error('not_found', 'Отзыв не найден.', status=404)

    if request.method == 'DELETE':
        delete_book_review(review)
        return api_success(status=204)

    data = parse_json_body(request)
    form = ReviewForm(data=data, instance=review)
    if not form.is_valid():
        return api_error('validation_error', 'Проверьте входные данные.', status=400, details=_form_errors(form))

    try:
        updated = save_book_review(review.book, user, form)
    except ValidationError as error:
        details = error.message_dict if hasattr(error, 'message_dict') else {'non_field_errors': error.messages}
        return api_error('validation_error', 'Проверьте входные данные.', status=400, details=details)

    return api_success(
        {
            'id': updated.id,
            'rating': updated.rating,
            'text': updated.text,
            'moderation_status': updated.get_moderation_status_display(),
            'created_at': _iso(updated.created_at),
        }
    )

@api_view(['GET', 'PATCH'])
def api_copy_detail(request, id: int):
    copy = get_copy_for_detail(id)
    if not copy:
        return api_error('not_found', 'Экземпляр не найден.', status=404)

    current_user = _auth_user_from_request(request)
    if request.method == 'PATCH':
        auth = _require_api_user(request)
        if isinstance(auth, JsonResponse):
            return auth
        if not _is_admin_user(auth):
            return api_error('forbidden', 'Только администратор может менять статус экземпляра.', status=403)

        data = parse_json_body(request)
        status_code = (data.get('status_code') or '').strip()
        if not status_code:
            return api_error(
                'validation_error',
                'Проверьте входные данные.',
                status=400,
                details={'status_code': ['Укажите код статуса.']},
            )
        status = CopyStatus.objects.filter(code=status_code).first()
        if status is None:
            return api_error(
                'validation_error',
                'Проверьте входные данные.',
                status=400,
                details={'status_code': ['Статус не найден.']},
            )
        note = (data.get('note') or '').strip()
        copy = update_copy_status(copy, status=status, actor=auth, note=note)
        return api_success(_serialize_copy_detail_data(copy, auth))

    return api_success(_serialize_copy_detail_data(copy, current_user))


@api_view(['POST'])
def api_copy_move_create(request, id: int):
    auth = _require_api_user(request)
    if isinstance(auth, JsonResponse):
        return auth
    user = auth
    copy = get_copy_for_detail(id)
    if not copy:
        return api_error('not_found', 'Экземпляр не найден.', status=404)

    data = parse_json_body(request)
    event_type_code = (data.get('event_type_code') or '').strip()
    if not event_type_code:
        return api_error('validation_error', 'Проверьте входные данные.', status=400, details={'event_type_code': ['Укажите тип события.']})
    form = MoveForm(
        data={
            'event_type': MoveEventType.objects.filter(code=event_type_code).values_list('id', flat=True).first(),
            'place_text': data.get('place_text') or '',
            'text': data.get('text') or '',
        }
    )
    if not form.is_valid():
        return api_error('validation_error', 'Проверьте входные данные.', status=400, details=_form_errors(form))
    try:
        move = create_copy_move(copy=copy, user=user, move_form=form, active_bind=get_active_bind(copy))
    except ValidationError as error:
        details = error.message_dict if hasattr(error, 'message_dict') else {'non_field_errors': error.messages}
        return api_error('validation_error', 'Проверьте входные данные.', status=400, details=details)

    move = Move.objects.select_related('copy__book', 'event_type', 'source', 'nfc_tag').get(pk=move.pk)
    return api_success(_serialize_move(move), status=201)


@api_view(['POST'])
def api_copy_bind_tag(request, id: int):
    auth = _require_api_user(request)
    if isinstance(auth, JsonResponse):
        return auth
    user = auth
    copy = get_copy_for_detail(id)
    if not copy:
        return api_error('not_found', 'Экземпляр не найден.', status=404)

    data = parse_json_body(request)
    form = NfcBindForm(data={'tag_uid': data.get('tag_uid') or ''})
    if not form.is_valid():
        return api_error('validation_error', 'Проверьте входные данные.', status=400, details=_form_errors(form))
    try:
        bind, created = bind_tag_to_copy(copy=copy, user=user, tag_uid=form.cleaned_data['tag_uid'], active_bind=get_active_bind(copy))
    except ValidationError as error:
        details = error.message_dict if hasattr(error, 'message_dict') else {'non_field_errors': error.messages}
        return api_error('nfc_tag_conflict', 'Конфликт NFC-привязки.', status=409, details=details)

    return api_success(
        {
            'copy_id': copy.id,
            'tag_uid': bind.tag.uid,
            'status': bind.tag.status.code,
            'already_active': not created,
            'started_at': _iso(bind.started_at),
        }
    )


@api_view(['POST'])
def api_copy_unbind_tag(request, id: int):
    auth = _require_api_user(request)
    if isinstance(auth, JsonResponse):
        return auth
    copy = get_copy_for_detail(id)
    if not copy:
        return api_error('not_found', 'Экземпляр не найден.', status=404)
    active_bind = get_active_bind(copy)
    if active_bind is None:
        return api_error('not_found', 'Для экземпляра нет активной NFC-привязки.', status=404)
    unbind_tag_from_copy(active_bind)
    active_bind.refresh_from_db()
    return api_success(
        {
            'copy_id': copy.id,
            'tag_uid': active_bind.tag.uid,
            'unbound': True,
            'ended_at': _iso(active_bind.ended_at),
        }
    )

@api_view(['GET'])
def api_events(request):
    event_type = (request.GET.get('type') or '').strip()
    page_number = request.GET.get('page') or 1
    qs = Move.objects.select_related('copy__book', 'event_type', 'source', 'nfc_tag').order_by('-date_time')
    if event_type:
        qs = qs.filter(event_type__code=event_type)

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(page_number)
    return api_success(
        {
            'items': [_serialize_move(move) for move in page_obj.object_list],
            'pagination': {
                'page': page_obj.number,
                'page_size': paginator.per_page,
                'total': paginator.count,
            },
        }
    )


@api_view(['GET'])
def api_recommendations(request):
    try:
        user, _session = authenticate_access_token(request.headers.get('Authorization'))
    except PermissionDenied as error:
        return api_error('unauthorized', str(error), status=401)

    return api_success({'items': get_recommendations_for_user(user)})


@api_view(['GET'])
def api_notifications(request):
    try:
        user, _session = authenticate_access_token(request.headers.get('Authorization'))
    except PermissionDenied as error:
        return api_error('unauthorized', str(error), status=401)

    return api_success({'items': get_notifications_for_user(user)})


@api_view(['POST'])
def api_notification_mark_read(request, id: int):
    auth = _require_api_user(request)
    if isinstance(auth, JsonResponse):
        return auth
    user = auth
    notification = Notification.objects.filter(id=id, user=user).first()
    if not notification:
        return api_error('not_found', 'Уведомление не найдено.', status=404)
    mark_notification_read(notification)
    return api_success({'id': notification.id, 'read': notification.is_read})


@api_view(['POST'])
def api_notifications_mark_all_read(request):
    auth = _require_api_user(request)
    if isinstance(auth, JsonResponse):
        return auth
    user = auth
    updated = mark_all_notifications_read(user)
    return api_success({'updated': updated})


@api_view(['POST'])
def api_scan(request):
    auth = _require_api_user(request)
    if isinstance(auth, JsonResponse):
        return auth
    user = auth
    data = parse_json_body(request)
    form = ScanForm(
        data={
            'copy_code': data.get('copy_code') or '',
            'tag_uid': data.get('tag_uid') or '',
            'place_text': data.get('place_text') or '',
            'text': data.get('text') or '',
        }
    )
    if not form.is_valid():
        return api_error('validation_error', 'Проверьте входные данные.', status=400, details=_form_errors(form))
    try:
        move = create_scan_event(user, form)
    except ValidationError as error:
        details = error.message_dict if hasattr(error, 'message_dict') else {'non_field_errors': error.messages}
        return api_error('scan_conflict', 'Не удалось зарегистрировать scan-событие.', status=409, details=details)
    move = Move.objects.select_related('event_type', 'nfc_tag').get(pk=move.pk)
    return api_success(
        {
            'move_id': move.id,
            'copy_id': move.copy_id,
            'copy_code': move.copy.code,
            'tag_uid': move.nfc_tag.uid if move.nfc_tag_id else None,
            'event_type': {
                'code': move.event_type.code,
                'title': move.event_type.title,
            },
            'date_time': _iso(move.date_time),
            'place_text': move.place_text,
            'text': move.text,
        },
        status=201,
    )
