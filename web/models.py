from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='booktrail_profile')
    avatar = models.CharField('Аватар', max_length=8, blank=True, default='')
    status = models.CharField('Статус', max_length=160, blank=True, default='')
    show_profile = models.BooleanField('Показывать профиль', default=True)
    share_reviews = models.BooleanField('Делиться отзывами', default=True)
    nfc_visibility = models.BooleanField('Показывать NFC-статус', default=False)
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self) -> str:
        return self.display_name

    @property
    def display_name(self) -> str:
        full_name = self.user.get_full_name().strip()
        return full_name or self.user.username

    def clean(self):
        if self.avatar:
            self.avatar = self.avatar.strip().upper()[:8]


class Role(models.Model):
    code = models.SlugField('Код', max_length=64, unique=True)
    title = models.CharField('Название', max_length=120)

    class Meta:
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'

    def __str__(self) -> str:
        return self.title


class UserRole(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='booktrail_roles', verbose_name='Пользователь')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_roles', verbose_name='Роль')
    assigned_at = models.DateTimeField('Назначено', auto_now_add=True)

    class Meta:
        verbose_name = 'Назначение роли'
        verbose_name_plural = 'Назначения ролей'
        constraints = [
            models.UniqueConstraint(fields=['user', 'role'], name='uniq_user_role'),
        ]

    def __str__(self) -> str:
        return f'{self.user} -> {self.role}'


class Genre(models.Model):
    name = models.CharField('Жанр', max_length=120, unique=True)
    slug = models.SlugField('Slug', max_length=120, unique=True)

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Language(models.Model):
    name = models.CharField('Язык', max_length=80, unique=True)
    code = models.CharField('Код', max_length=16, unique=True)

    class Meta:
        verbose_name = 'Язык'
        verbose_name_plural = 'Языки'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Author(models.Model):
    name = models.CharField('Автор', max_length=160, unique=True)

    class Meta:
        verbose_name = 'Автор'
        verbose_name_plural = 'Авторы'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class CopyStatus(models.Model):
    code = models.SlugField('Код', max_length=32, unique=True)
    title = models.CharField('Название', max_length=120)

    class Meta:
        verbose_name = 'Статус экземпляра'
        verbose_name_plural = 'Статусы экземпляров'
        ordering = ['title']

    def __str__(self) -> str:
        return self.title


class NfcTagStatus(models.Model):
    code = models.SlugField('Код', max_length=32, unique=True)
    title = models.CharField('Название', max_length=120)

    class Meta:
        verbose_name = 'Статус NFC-метки'
        verbose_name_plural = 'Статусы NFC-меток'
        ordering = ['title']

    def __str__(self) -> str:
        return self.title


class MoveEventType(models.Model):
    code = models.SlugField('Код', max_length=32, unique=True)
    title = models.CharField('Название', max_length=120)

    class Meta:
        verbose_name = 'Тип события'
        verbose_name_plural = 'Типы событий'
        ordering = ['title']

    def __str__(self) -> str:
        return self.title


class MoveSource(models.Model):
    code = models.SlugField('Код', max_length=32, unique=True)
    title = models.CharField('Название', max_length=160)

    class Meta:
        verbose_name = 'Источник события'
        verbose_name_plural = 'Источники событий'
        ordering = ['title']

    def __str__(self) -> str:
        return self.title


class ReviewModerationStatus(models.Model):
    code = models.SlugField('Код', max_length=32, unique=True)
    title = models.CharField('Название', max_length=120)

    class Meta:
        verbose_name = 'Статус модерации'
        verbose_name_plural = 'Статусы модерации'
        ordering = ['title']

    def __str__(self) -> str:
        return self.title


class NotificationKind(models.Model):
    code = models.SlugField('Код', max_length=32, unique=True)
    title = models.CharField('Название', max_length=120)

    class Meta:
        verbose_name = 'Тип уведомления'
        verbose_name_plural = 'Типы уведомлений'
        ordering = ['title']

    def __str__(self) -> str:
        return self.title


class Book(models.Model):
    title = models.CharField('Название', max_length=240)
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, blank=True, related_name='books', verbose_name='Жанр')
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True, related_name='books', verbose_name='Язык')
    year = models.IntegerField('Год', null=True, blank=True)
    description = models.TextField('Описание', blank=True, default='')
    cover = models.CharField('Обложка', max_length=240, blank=True, default='web/img/placeholder-cover.svg')
    accent = models.CharField('Акцент', max_length=32, blank=True, default='blue')
    isbn = models.CharField('ISBN', max_length=32, null=True, blank=True, unique=True)
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    authors = models.ManyToManyField(Author, through='BookAuthor', related_name='books', verbose_name='Авторы')

    class Meta:
        verbose_name = 'Книга'
        verbose_name_plural = 'Книги'

    def __str__(self) -> str:
        return self.title

    @property
    def author_names(self) -> list[str]:
        authors = getattr(self, 'prefetched_authors', None)
        if authors is not None:
            return [author.name for author in authors]
        return list(self.authors.order_by('book_authors__sort_order', 'name').values_list('name', flat=True))


class BookAuthor(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='book_authors', verbose_name='Книга')
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='book_authors', verbose_name='Автор')
    sort_order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Автор книги'
        verbose_name_plural = 'Авторы книг'
        ordering = ['sort_order', 'id']
        constraints = [
            models.UniqueConstraint(fields=['book', 'author'], name='uniq_book_author'),
            models.UniqueConstraint(fields=['book', 'sort_order'], name='uniq_book_author_order'),
        ]

    def __str__(self) -> str:
        return f'{self.book} -> {self.author}'


class Copy(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='copies', verbose_name='Книга')
    code = models.CharField('Код экземпляра', max_length=64, unique=True, db_index=True)
    status = models.ForeignKey(CopyStatus, on_delete=models.PROTECT, related_name='copies', verbose_name='Статус')
    holder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='held_copies',
        verbose_name='Текущий держатель',
    )
    initiator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_copies',
        verbose_name='Инициатор',
    )
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        verbose_name = 'Экземпляр'
        verbose_name_plural = 'Экземпляры'

    def __str__(self) -> str:
        return f'{self.code} ({self.book.title})'

    @property
    def copy_code(self) -> str:
        return self.code

    def get_status_display(self) -> str:
        return self.status.title


class NfcTag(models.Model):
    uid = models.CharField('UID метки', max_length=64, null=True, blank=True, unique=True)
    status = models.ForeignKey(NfcTagStatus, on_delete=models.PROTECT, related_name='tags', verbose_name='Статус')
    created_at = models.DateTimeField('Создана', auto_now_add=True)

    class Meta:
        verbose_name = 'NFC-метка'
        verbose_name_plural = 'NFC-метки'

    def __str__(self) -> str:
        return self.uid or f'NFC tag #{self.pk}'

    def get_status_display(self) -> str:
        return self.status.title


class TagBind(models.Model):
    copy = models.ForeignKey(Copy, on_delete=models.CASCADE, related_name='tag_binds', verbose_name='Экземпляр книги')
    tag = models.ForeignKey(NfcTag, on_delete=models.CASCADE, related_name='binds', verbose_name='NFC-метка')
    started_at = models.DateTimeField('Дата привязки')
    ended_at = models.DateTimeField('Дата окончания', null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tag_binds_created',
        verbose_name='Создал',
    )

    class Meta:
        verbose_name = 'Привязка NFC-метки'
        verbose_name_plural = 'Привязки NFC-меток'
        constraints = [
            models.CheckConstraint(
                condition=Q(ended_at__isnull=True) | Q(ended_at__gte=models.F('started_at')),
                name='tag_bind_end_after_start',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.copy.code} <-> {self.tag}'

    def clean(self):
        errors = {}

        if self.ended_at and self.started_at and self.ended_at < self.started_at:
            errors['ended_at'] = 'Дата окончания не может быть раньше даты привязки.'

        if self.tag_id and self.ended_at is None:
            active_for_tag = TagBind.objects.filter(tag_id=self.tag_id, ended_at__isnull=True).exclude(pk=self.pk).select_related('copy').first()
            if active_for_tag:
                if active_for_tag.copy_id == self.copy_id:
                    errors['tag'] = 'Эта NFC-метка уже активно привязана к текущему экземпляру.'
                else:
                    errors['tag'] = f'Эта NFC-метка уже активно привязана к экземпляру {active_for_tag.copy.code}.'

            if self.tag.status.code == 'archived':
                errors['tag'] = 'Архивированную NFC-метку нельзя привязать.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.ended_at is None:
            TagBind.objects.filter(copy=self.copy, ended_at__isnull=True).exclude(pk=self.pk).update(ended_at=self.started_at)
        super().save(*args, **kwargs)

        if self.ended_at is None and self.tag.status.code != 'archived':
            bound_status = NfcTagStatus.objects.filter(code='bound').first()
            if bound_status and self.tag.status_id != bound_status.id:
                self.tag.status = bound_status
                self.tag.save(update_fields=['status'])
        elif self.ended_at is not None and self.tag.status.code == 'bound':
            has_other_active = TagBind.objects.filter(tag=self.tag, ended_at__isnull=True).exclude(pk=self.pk).exists()
            available_status = NfcTagStatus.objects.filter(code='available').first()
            if not has_other_active and available_status:
                self.tag.status = available_status
                self.tag.save(update_fields=['status'])


class Move(models.Model):
    copy = models.ForeignKey(Copy, on_delete=models.CASCADE, related_name='moves', verbose_name='Экземпляр книги', db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='moves', verbose_name='Пользователь')
    event_type = models.ForeignKey(MoveEventType, on_delete=models.PROTECT, related_name='moves', verbose_name='Тип события')
    date_time = models.DateTimeField('Дата/время', db_index=True)
    place_text = models.CharField('Место', max_length=160, blank=True, default='')
    text = models.TextField('Комментарий', blank=True, default='')
    payload = models.TextField('Данные', blank=True, default='')
    source = models.ForeignKey(MoveSource, on_delete=models.PROTECT, related_name='moves', verbose_name='Источник')
    nfc_tag = models.ForeignKey(NfcTag, on_delete=models.SET_NULL, null=True, blank=True, related_name='moves', verbose_name='NFC-метка')

    class Meta:
        verbose_name = 'Перемещение'
        verbose_name_plural = 'Перемещения'

    def __str__(self) -> str:
        return f'{self.copy.code}: {self.event_type.title} @ {self.date_time:%Y-%m-%d %H:%M}'

    def get_event_type_display(self) -> str:
        return self.event_type.title

    def clean(self):
        if self.nfc_tag_id:
            active_bind = TagBind.objects.filter(tag_id=self.nfc_tag_id, ended_at__isnull=True).exclude(copy_id=self.copy_id).select_related('copy').first()
            if active_bind:
                raise ValidationError({'nfc_tag': f'NFC-метка сейчас привязана к экземпляру {active_bind.copy.code}, а не к выбранному экземпляру.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews', verbose_name='Книга', db_index=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews', verbose_name='Автор')
    rating = models.IntegerField('Оценка', default=0)
    text = models.TextField('Текст', blank=True, default='')
    moderation_status = models.ForeignKey(ReviewModerationStatus, on_delete=models.PROTECT, related_name='reviews', verbose_name='Статус модерации')
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        constraints = [
            models.UniqueConstraint(fields=['book', 'author'], name='uniq_review_per_user_book'),
            models.CheckConstraint(condition=Q(rating__gte=1) & Q(rating__lte=5), name='review_rating_between_1_and_5'),
        ]

    def __str__(self) -> str:
        return f'Отзыв {self.book.title} ({self.rating})'

    def get_moderation_status_display(self) -> str:
        return self.moderation_status.title

    def clean(self):
        if self.rating < 1 or self.rating > 5:
            raise ValidationError({'rating': 'Оценка должна быть от 1 до 5.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Recommendation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recommendations', verbose_name='Пользователь', db_index=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='recommendations', verbose_name='Книга')
    score = models.FloatField('Скор', default=0.0)
    explanation = models.TextField('Пояснение', blank=True, default='')
    created_at = models.DateTimeField('Создана', auto_now_add=True)

    class Meta:
        verbose_name = 'Рекомендация'
        verbose_name_plural = 'Рекомендации'
        constraints = [
            models.UniqueConstraint(fields=['user', 'book'], name='uniq_recommendation_per_user_book'),
        ]

    def __str__(self) -> str:
        return f'{self.user.username}: {self.book.title} ({self.score:.2f})'


class AuthSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='auth_sessions', verbose_name='Пользователь')
    device = models.CharField('Устройство', max_length=120, blank=True, default='')
    location = models.CharField('Локация', max_length=120, blank=True, default='')
    last_seen = models.DateTimeField('Последняя активность')
    refresh_token_hash = models.CharField('Хэш refresh токена', max_length=80, unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    revoked = models.BooleanField('Отозвана', default=False)
    current = models.BooleanField('Текущая', default=False)

    class Meta:
        verbose_name = 'Сессия'
        verbose_name_plural = 'Сессии'

    def __str__(self) -> str:
        return f'{self.user.username}: {self.device}'


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications', verbose_name='Получатель', db_index=True)
    title = models.CharField('Заголовок', max_length=160, blank=True, default='')
    text = models.TextField('Текст', blank=True, default='')
    kind = models.ForeignKey(NotificationKind, on_delete=models.PROTECT, related_name='notifications', verbose_name='Тип')
    is_read = models.BooleanField('Прочитано', default=False)
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'

    def __str__(self) -> str:
        return self.title or f'Уведомление #{self.pk}'

    def get_kind_display(self) -> str:
        return self.kind.title
