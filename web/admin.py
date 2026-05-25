from django.contrib import admin
from django.utils import timezone

from .models import (
    AuthSession,
    Author,
    Book,
    BookAuthor,
    Copy,
    CopyStatus,
    Genre,
    Language,
    Move,
    MoveEventType,
    MoveSource,
    NfcTag,
    NfcTagStatus,
    Notification,
    NotificationKind,
    Recommendation,
    Review,
    ReviewModerationStatus,
    Role,
    TagBind,
    UserProfile,
    UserRole,
)


def _get_status(model, code: str):
    return model.objects.filter(code=code).first()


class BookAuthorInline(admin.TabularInline):
    model = BookAuthor
    extra = 0
    autocomplete_fields = ('author',)
    ordering = ('sort_order', 'id')


class CopyInline(admin.TabularInline):
    model = Copy
    extra = 0
    fields = ('code', 'status', 'initiator', 'created_at')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('status', 'initiator')
    show_change_link = True


class TagBindInline(admin.TabularInline):
    model = TagBind
    extra = 0
    fields = ('tag', 'started_at', 'ended_at', 'created_by')
    readonly_fields = ('started_at', 'ended_at')
    autocomplete_fields = ('tag', 'created_by')
    show_change_link = True


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'display_name', 'avatar', 'show_profile', 'share_reviews', 'nfc_visibility', 'updated_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    list_filter = ('show_profile', 'share_reviews', 'nfc_visibility')
    autocomplete_fields = ('user',)
    list_select_related = ('user',)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'title')
    search_fields = ('code', 'title')


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'role', 'assigned_at')
    search_fields = ('user__username', 'user__email', 'role__code')
    autocomplete_fields = ('user', 'role')
    list_select_related = ('user', 'role')


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code')
    search_fields = ('name', 'code')


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'genre', 'language', 'year', 'isbn', 'created_at')
    search_fields = ('title', 'isbn', 'authors__name')
    list_filter = ('genre', 'language', 'year')
    autocomplete_fields = ('genre', 'language')
    inlines = [BookAuthorInline, CopyInline]
    list_select_related = ('genre', 'language')
    date_hierarchy = 'created_at'


@admin.register(BookAuthor)
class BookAuthorAdmin(admin.ModelAdmin):
    list_display = ('id', 'book', 'author', 'sort_order')
    search_fields = ('book__title', 'author__name')
    autocomplete_fields = ('book', 'author')
    list_select_related = ('book', 'author')


@admin.register(Copy)
class CopyAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'book', 'status', 'initiator', 'created_at')
    search_fields = ('code', 'book__title', 'initiator__username', 'initiator__email')
    list_filter = ('status', 'created_at')
    autocomplete_fields = ('book', 'status', 'initiator')
    list_select_related = ('book', 'status', 'initiator')
    inlines = [TagBindInline]
    date_hierarchy = 'created_at'


@admin.register(CopyStatus)
class CopyStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'title')
    search_fields = ('code', 'title')


@admin.action(description='Отметить метки как свободные')
def make_tags_available(modeladmin, request, queryset):
    status = _get_status(NfcTagStatus, 'available')
    if status:
        queryset.update(status=status)


@admin.action(description='Архивировать метки')
def archive_tags(modeladmin, request, queryset):
    status = _get_status(NfcTagStatus, 'archived')
    if status:
        queryset.update(status=status)


@admin.register(NfcTag)
class NfcTagAdmin(admin.ModelAdmin):
    list_display = ('id', 'uid', 'status', 'created_at')
    search_fields = ('uid',)
    list_filter = ('status', 'created_at')
    autocomplete_fields = ('status',)
    list_select_related = ('status',)
    actions = [make_tags_available, archive_tags]
    date_hierarchy = 'created_at'


@admin.register(NfcTagStatus)
class NfcTagStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'title')
    search_fields = ('code', 'title')


@admin.action(description='Завершить выбранные активные привязки')
def close_active_binds(modeladmin, request, queryset):
    active_binds = queryset.filter(ended_at__isnull=True).select_related('tag')
    for bind in active_binds:
        bind.ended_at = timezone.now()
        bind.save(update_fields=['ended_at'])


@admin.register(TagBind)
class TagBindAdmin(admin.ModelAdmin):
    list_display = ('id', 'copy', 'tag', 'started_at', 'ended_at', 'created_by')
    search_fields = ('copy__code', 'tag__uid', 'created_by__username', 'created_by__email')
    list_filter = ('ended_at', 'started_at')
    autocomplete_fields = ('copy', 'tag', 'created_by')
    list_select_related = ('copy', 'tag', 'created_by')
    actions = [close_active_binds]
    date_hierarchy = 'started_at'


@admin.register(Move)
class MoveAdmin(admin.ModelAdmin):
    list_display = ('id', 'copy', 'event_type', 'date_time', 'place_text', 'user', 'source')
    search_fields = ('copy__code', 'copy__book__title', 'place_text', 'text', 'payload', 'user__username', 'user__email')
    list_filter = ('event_type', 'source', 'date_time')
    autocomplete_fields = ('copy', 'event_type', 'user', 'source', 'nfc_tag')
    list_select_related = ('copy', 'event_type', 'user', 'source', 'nfc_tag')
    date_hierarchy = 'date_time'


@admin.register(MoveEventType)
class MoveEventTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'title')
    search_fields = ('code', 'title')


@admin.register(MoveSource)
class MoveSourceAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'title')
    search_fields = ('code', 'title')


@admin.action(description='Опубликовать выбранные отзывы')
def publish_reviews(modeladmin, request, queryset):
    status = _get_status(ReviewModerationStatus, 'published')
    if status:
        queryset.update(moderation_status=status)


@admin.action(description='Отправить выбранные отзывы на модерацию')
def pend_reviews(modeladmin, request, queryset):
    status = _get_status(ReviewModerationStatus, 'pending')
    if status:
        queryset.update(moderation_status=status)


@admin.action(description='Отклонить выбранные отзывы')
def reject_reviews(modeladmin, request, queryset):
    status = _get_status(ReviewModerationStatus, 'rejected')
    if status:
        queryset.update(moderation_status=status)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'book', 'author', 'rating', 'moderation_status', 'created_at')
    search_fields = ('book__title', 'author__username', 'author__email', 'text')
    list_filter = ('moderation_status', 'rating', 'created_at')
    autocomplete_fields = ('book', 'author', 'moderation_status')
    list_select_related = ('book', 'author', 'moderation_status')
    actions = [publish_reviews, pend_reviews, reject_reviews]
    date_hierarchy = 'created_at'


@admin.register(ReviewModerationStatus)
class ReviewModerationStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'title')
    search_fields = ('code', 'title')


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'book', 'score', 'created_at')
    search_fields = ('user__username', 'user__email', 'book__title')
    autocomplete_fields = ('user', 'book')
    list_select_related = ('user', 'book')
    date_hierarchy = 'created_at'


@admin.action(description='Отозвать выбранные сессии')
def revoke_sessions(modeladmin, request, queryset):
    queryset.update(revoked=True, current=False)


@admin.register(AuthSession)
class AuthSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'device', 'location', 'last_seen', 'revoked', 'current')
    search_fields = ('user__username', 'user__email', 'device', 'location', 'refresh_token_hash')
    list_filter = ('revoked', 'current')
    autocomplete_fields = ('user',)
    list_select_related = ('user',)
    actions = [revoke_sessions]
    date_hierarchy = 'last_seen'


@admin.action(description='Отметить выбранные уведомления как прочитанные')
def mark_notifications_read(modeladmin, request, queryset):
    queryset.update(is_read=True)


@admin.action(description='Отметить выбранные уведомления как непрочитанные')
def mark_notifications_unread(modeladmin, request, queryset):
    queryset.update(is_read=False)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'kind', 'is_read', 'created_at')
    search_fields = ('user__username', 'user__email', 'title', 'text')
    list_filter = ('is_read', 'kind', 'created_at')
    autocomplete_fields = ('user', 'kind')
    list_select_related = ('user', 'kind')
    actions = [mark_notifications_read, mark_notifications_unread]
    date_hierarchy = 'created_at'


@admin.register(NotificationKind)
class NotificationKindAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'title')
    search_fields = ('code', 'title')
