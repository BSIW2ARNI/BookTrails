from __future__ import annotations

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import (
    Copy,
    CopyStatus,
    Move,
    MoveEventType,
    MoveSource,
    NfcTag,
    NfcTagStatus,
    Notification,
    Review,
    ReviewModerationStatus,
    TagBind,
)
from .recommendation_engine import persist_recommendations_for_user
from .selectors import get_active_bind


def _get_or_create_reference(model, code: str, title: str):
    return model.objects.get_or_create(code=code, defaults={'title': title})[0]


def get_move_source(code: str = 'booktrail_route', title: str = 'Маршрут BookTrail') -> MoveSource:
    return _get_or_create_reference(MoveSource, code, title)


def get_move_event_type(code: str, title: str) -> MoveEventType:
    return _get_or_create_reference(MoveEventType, code, title)


def get_review_status(code: str = 'published', title: str = 'Опубликован') -> ReviewModerationStatus:
    return _get_or_create_reference(ReviewModerationStatus, code, title)


def get_tag_status(code: str, title: str) -> NfcTagStatus:
    return _get_or_create_reference(NfcTagStatus, code, title)


def get_copy_status(code: str, title: str) -> CopyStatus:
    return _get_or_create_reference(CopyStatus, code, title)


def save_book_review(book, user: User, review_form) -> Review:
    review = review_form.save(commit=False)
    review.book = book
    review.author = user
    review.moderation_status = get_review_status()
    review.save()
    persist_recommendations_for_user(user, limit=10)
    return review


def delete_book_review(review: Review | None) -> bool:
    if review is None:
        return False
    author = review.author
    review.delete()
    if author:
        persist_recommendations_for_user(author, limit=10)
    return True


def update_profile(profile_form):
    return profile_form.save()


def create_copy_move(copy: Copy, user: User, move_form, active_bind: TagBind | None = None) -> Move:
    return Move.objects.create(
        copy=copy,
        user=user,
        event_type=move_form.cleaned_data['event_type'],
        date_time=timezone.now(),
        place_text=move_form.cleaned_data['place_text'],
        text=move_form.cleaned_data['text'],
        source=get_move_source(),
        nfc_tag=active_bind.tag if active_bind else None,
    )


def update_copy_status(copy: Copy, *, status: CopyStatus, actor: User, note: str = '') -> Copy:
    active_bind = get_active_bind(copy)
    copy.status = status
    if status.code != 'with_reader':
        copy.holder = None
    copy.save(update_fields=['status', 'holder'])

    Move.objects.create(
        copy=copy,
        user=actor,
        event_type=get_move_event_type('transfer', 'Передача'),
        date_time=timezone.now(),
        place_text='Ручное изменение статуса',
        text=note or f'Статус экземпляра изменён на "{status.title}".',
        source=get_move_source(),
        nfc_tag=active_bind.tag if active_bind else None,
        payload=f'status={status.code}',
    )
    return copy


def bind_tag_to_copy(copy: Copy, user: User, tag_uid: str, active_bind: TagBind | None = None) -> tuple[TagBind, bool]:
    tag = NfcTag.objects.filter(uid__iexact=tag_uid).select_related('status').first()
    bound_status = get_tag_status('bound', 'Привязана')

    if tag and tag.status.code == 'archived':
        raise ValidationError({'tag_uid': 'Эта NFC-метка архивирована.'})

    if active_bind and tag and active_bind.tag_id == tag.id:
        if active_bind.tag.status_id != bound_status.id:
            active_bind.tag.status = bound_status
            active_bind.tag.save(update_fields=['status'])
        return active_bind, False

    with transaction.atomic():
        if active_bind:
            active_bind.ended_at = timezone.now()
            active_bind.save(update_fields=['ended_at'])

        if tag is None:
            tag = NfcTag.objects.create(uid=tag_uid, status=bound_status)
        elif tag.status_id != bound_status.id:
            tag.status = bound_status
            tag.save(update_fields=['status'])

        new_bind = TagBind.objects.create(
            copy=copy,
            tag=tag,
            started_at=timezone.now(),
            created_by=user,
        )

    return new_bind, True


def unbind_tag_from_copy(active_bind: TagBind | None) -> bool:
    if active_bind is None:
        return False

    with transaction.atomic():
        active_bind.ended_at = timezone.now()
        active_bind.save(update_fields=['ended_at'])

    return True


def mark_all_notifications_read(user: User) -> int:
    return Notification.objects.filter(user=user, is_read=False).update(is_read=True)


def mark_notification_read(notification: Notification) -> bool:
    if notification.is_read:
        return False
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    return True


def create_scan_event(user: User, scan_form) -> Move:
    copy_code = scan_form.cleaned_data['copy_code']
    tag_uid = scan_form.cleaned_data['tag_uid']
    tag = None
    active_bind = None

    if tag_uid:
        active_bind = (
            TagBind.objects.filter(tag__uid__iexact=tag_uid, ended_at__isnull=True)
            .select_related('copy', 'tag')
            .first()
        )
        if active_bind is None:
            raise ValidationError({'tag_uid': 'Активная привязка для этой метки не найдена.'})
        tag = active_bind.tag

    copy = None
    if copy_code:
        copy = Copy.objects.filter(code__iexact=copy_code).first()
        if copy is None:
            raise ValidationError({'copy_code': 'Экземпляр с таким кодом не найден.'})

    if active_bind and copy and active_bind.copy_id != copy.id:
        raise ValidationError('UID метки и код экземпляра указывают на разные экземпляры.')

    copy = copy or active_bind.copy
    if tag is None:
        current_bind = get_active_bind(copy)
        tag = current_bind.tag if current_bind else None

    copy.status = get_copy_status('with_reader', 'У читателя')
    copy.holder = user
    copy.save(update_fields=['status', 'holder'])

    return Move.objects.create(
        copy=copy,
        user=user,
        event_type=get_move_event_type('scan', 'Сканирование'),
        date_time=timezone.now(),
        place_text=scan_form.cleaned_data['place_text'],
        text=scan_form.cleaned_data['text'],
        source=get_move_source(),
        nfc_tag=tag,
        payload=f'scan_uid={tag.uid};holder={user.id}' if tag else f'holder={user.id}',
    )
