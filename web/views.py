from __future__ import annotations

import re
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404, JsonResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import LoginForm, MoveForm, NfcBindForm, ProfileForm, RegisterForm, ReviewForm, ScanForm
from .models import Notification
from .selectors import (
    get_active_bind,
    get_book_copies,
    get_book_for_detail,
    get_book_reviews,
    get_catalog_data,
    get_copy_for_detail,
    get_copy_movements,
    get_copy_nfc_state,
    get_events_feed_data,
    get_latest_events,
    get_notifications_for_user,
    get_profile_dashboard,
    get_recommendations_for_user,
    get_related_books,
    get_scan_history,
    get_user_review_for_book,
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
    update_profile,
)
from .utils import ensure_profile, get_current_user


_SCREENSHOT_SAFE_RE = re.compile(r'[^0-9A-Za-zА-Яа-я_-]+')
_SCREENSHOT_UNDERSCORE_RE = re.compile(r'_{3,}')

HOW_IT_WORKS = [
    {'title': 'Экземпляр', 'text': 'Каждая физическая книга получает собственный код и маршрут внутри BookTrail.'},
    {'title': 'NFC', 'text': 'Метка связывает экземпляр с цифровой карточкой и ускоряет фиксацию событий.'},
    {'title': 'События', 'text': 'Сканирования, передачи и остановки складываются в живую ленту движения книги.'},
    {'title': 'Отзывы', 'text': 'Читатели оставляют впечатления, которые становятся частью контекста книги.'},
    {'title': 'Рекомендации', 'text': 'Платформа подсказывает похожие книги на основе маршрутов и семантики отзывов.'},
]


def _next_url(request, fallback: str) -> str:
    redirect_to = request.POST.get('next') or request.GET.get('next')
    if redirect_to and url_has_allowed_host_and_scheme(
        redirect_to,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect_to
    return reverse(fallback)


def _book_detail_url(book_id: int) -> str:
    return f"{reverse('web:book_detail', args=[book_id])}#reviews"


def _copy_detail_url(copy_id: int) -> str:
    return f"{reverse('web:copy_detail', args=[copy_id])}#copy-actions"


def _normalize_screenshot_path(url_path: str) -> str:
    path = (url_path or '').split('?', 1)[0].split('#', 1)[0].strip('/')
    if not path:
        return 'home'

    path = path.replace('/', '__')
    path = _SCREENSHOT_SAFE_RE.sub('_', path)
    path = _SCREENSHOT_UNDERSCORE_RE.sub('_', path).strip('_')
    return path or 'home'


def _apply_validation_errors(form, error: ValidationError):
    if hasattr(error, 'message_dict'):
        for field, messages_list in error.message_dict.items():
            target_field = field if field in form.fields else None
            for message in messages_list:
                form.add_error(target_field, message)
        return

    for message in error.messages:
        form.add_error(None, message)


def landing(request):
    return render(request, 'landing.html', {'latest_events': get_latest_events(), 'how_it_works': HOW_IT_WORKS})


@require_POST
def save_page_screenshot(request):
    image = request.FILES['image']
    url_path = request.POST['url_path']

    prefix = _normalize_screenshot_path(url_path)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{prefix}_{timestamp}.png'

    screenshots_dir = settings.MEDIA_ROOT / 'auto_screenshots'
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    destination = screenshots_dir / filename
    with destination.open('wb+') as output:
        for chunk in image.chunks():
            output.write(chunk)

    return JsonResponse({'ok': True, 'filename': filename, 'url_path': url_path})


def catalog(request):
    query = (request.GET.get('q') or '').strip()
    genre = request.GET.get('genre')
    language = request.GET.get('language')
    return render(request, 'catalog.html', get_catalog_data(query=query, genre=genre, language=language))


def book_detail(request, id: int):
    book = get_book_for_detail(id)
    if not book:
        raise Http404('Book not found')

    user_review = None
    review_form = None
    if request.user.is_authenticated:
        user_review = get_user_review_for_book(book, request.user)
        review_form = ReviewForm(instance=user_review)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(f"{reverse('web:auth_login')}?next={request.path}")

        action = request.POST.get('action')
        if action == 'save_review':
            review_form = ReviewForm(request.POST, instance=user_review)
            if review_form.is_valid():
                try:
                    save_book_review(book, request.user, review_form)
                except ValidationError as error:
                    _apply_validation_errors(review_form, error)
                    messages.error(request, 'Проверьте форму отзыва.')
                else:
                    messages.success(request, 'Отзыв сохранён.')
                    return redirect(_book_detail_url(book.id))
            else:
                messages.error(request, 'Проверьте форму отзыва.')
        elif action == 'delete_review':
            if delete_book_review(user_review):
                messages.success(request, 'Отзыв удалён.')
                return redirect(_book_detail_url(book.id))
            messages.error(request, 'Ваш отзыв для этой книги не найден.')

    return render(
        request,
        'book_detail.html',
        {
            'book': book,
            'reviews': get_book_reviews(book, request.user if request.user.is_authenticated else None),
            'copies': get_book_copies(book),
            'related_books': get_related_books(book),
            'review_form': review_form,
            'user_review': user_review,
        },
    )


def copy_detail(request, id: int):
    copy = get_copy_for_detail(id)
    if not copy:
        raise Http404('Copy not found')

    active_bind = get_active_bind(copy)
    move_form = MoveForm()
    nfc_bind_form = NfcBindForm()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(f"{reverse('web:auth_login')}?next={request.path}")

        action = request.POST.get('action')
        if action == 'add_move':
            move_form = MoveForm(request.POST)
            if move_form.is_valid():
                try:
                    create_copy_move(copy=copy, user=request.user, move_form=move_form, active_bind=active_bind)
                except ValidationError as error:
                    _apply_validation_errors(move_form, error)
                    messages.error(request, 'Проверьте форму события.')
                else:
                    messages.success(request, 'Событие добавлено в маршрут экземпляра.')
                    return redirect(_copy_detail_url(copy.id))
            else:
                messages.error(request, 'Проверьте форму события.')
        elif action == 'bind_tag':
            nfc_bind_form = NfcBindForm(request.POST)
            if nfc_bind_form.is_valid():
                try:
                    _, created = bind_tag_to_copy(
                        copy=copy,
                        user=request.user,
                        tag_uid=nfc_bind_form.cleaned_data['tag_uid'],
                        active_bind=active_bind,
                    )
                except ValidationError as error:
                    _apply_validation_errors(nfc_bind_form, error)
                    messages.error(request, 'Проверьте UID NFC-метки.')
                else:
                    if created:
                        messages.success(request, 'NFC-метка привязана к экземпляру.')
                    else:
                        messages.info(request, 'Эта метка уже активна для текущего экземпляра.')
                    return redirect(_copy_detail_url(copy.id))
            if not nfc_bind_form.errors:
                messages.error(request, 'Проверьте UID NFC-метки.')
        elif action == 'unbind_tag':
            if unbind_tag_from_copy(active_bind):
                messages.success(request, 'NFC-метка отвязана.')
                return redirect(_copy_detail_url(copy.id))
            messages.error(request, 'Для этого экземпляра нет активной NFC-привязки.')

    active_bind, nfc = get_copy_nfc_state(copy)
    return render(
        request,
        'copy_detail.html',
        {
            'copy': copy,
            'book': copy.book,
            'movements': get_copy_movements(copy),
            'nfc': nfc,
            'active_bind': active_bind,
            'move_form': move_form,
            'nfc_bind_form': nfc_bind_form,
        },
    )


def events_feed(request):
    event_type = request.GET.get('type')
    return render(request, 'events.html', get_events_feed_data(event_type=event_type, page_number=request.GET.get('page')))


@login_required(login_url='web:auth_login')
def recommendations(request):
    user = get_current_user(request)
    return render(request, 'recommendations.html', {'recommendations': get_recommendations_for_user(user)})


@login_required(login_url='web:auth_login')
def notifications_page(request):
    user = get_current_user(request)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'mark_all_read':
            updated = mark_all_notifications_read(user)
            if updated:
                messages.success(request, 'Все уведомления отмечены как прочитанные.')
            else:
                messages.info(request, 'Новых уведомлений нет.')
            return redirect('web:notifications')
        if action == 'mark_read':
            notification = get_object_or_404(Notification, pk=request.POST.get('notification_id'), user=user)
            if mark_notification_read(notification):
                messages.success(request, 'Уведомление отмечено как прочитанное.')
            else:
                messages.info(request, 'Уведомление уже было прочитано.')
            return redirect('web:notifications')

    return render(request, 'notifications.html', {'notifications': get_notifications_for_user(user)})


@login_required(login_url='web:auth_login')
def profile(request):
    user = get_current_user(request)
    profile = ensure_profile(user)
    profile_form = ProfileForm(user=user, profile=profile, data=request.POST or None)

    if request.method == 'POST':
        if profile_form.is_valid():
            profile = update_profile(profile_form)
            messages.success(request, 'Профиль обновлён.')
            return redirect('web:profile')
        messages.error(request, 'Проверьте форму профиля.')

    dashboard = get_profile_dashboard(user, profile)
    dashboard['profile_form'] = profile_form
    return render(request, 'profile.html', dashboard)


def auth_login(request):
    if request.user.is_authenticated:
        return redirect('web:profile')

    form = LoginForm(request=request, data=request.POST or None)
    next_url = request.POST.get('next') or request.GET.get('next') or ''
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        django_login(request, user)
        ensure_profile(user)
        return redirect(_next_url(request, 'web:profile'))

    return render(request, 'auth_login.html', {'form': form, 'next_url': next_url})


def auth_register(request):
    if request.user.is_authenticated:
        return redirect('web:profile')

    form = RegisterForm(request.POST or None)
    next_url = request.POST.get('next') or request.GET.get('next') or ''
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        ensure_profile(user)
        django_login(request, user)
        return redirect(_next_url(request, 'web:profile'))

    return render(request, 'auth_register.html', {'form': form, 'next_url': next_url})


@require_POST
@login_required(login_url='web:auth_login')
def auth_logout(request):
    django_logout(request)
    return redirect('web:landing')


@login_required(login_url='web:auth_login')
def scan_placeholder(request):
    user = get_current_user(request)
    scan_form = ScanForm(request.POST or None)
    if request.method == 'POST':
        if scan_form.is_valid():
            try:
                create_scan_event(user, scan_form)
            except ValidationError as error:
                _apply_validation_errors(scan_form, error)
                messages.error(request, 'Проверьте данные сканирования.')
            else:
                messages.success(request, 'Сканирование сохранено в маршрут книги.')
                return redirect('web:scan')

    return render(request, 'scan_placeholder.html', {'scans': get_scan_history(user), 'scan_form': scan_form})
