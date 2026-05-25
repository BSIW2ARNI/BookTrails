from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from web.models import (
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
    UserRole,
)
from web.utils import ensure_profile


def _dt(days_ago: int, minutes_offset: int = 0) -> datetime:
    return timezone.now() - timedelta(days=days_ago, minutes=minutes_offset)


DEMO_USER_PASSWORD = 'StrongPass123'


class Command(BaseCommand):
    help = 'Seed BookTrail demo data (idempotent).'

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(42)

        copy_statuses = {
            code: CopyStatus.objects.get_or_create(code=code, defaults={'title': title})[0]
            for code, title in [
                ('in_transit', 'В движении'),
                ('with_reader', 'У читателя'),
                ('waiting', 'Ожидает следующего читателя'),
                ('community_shelf', 'На полке сообщества'),
                ('processing', 'В обработке'),
            ]
        }
        tag_statuses = {
            code: NfcTagStatus.objects.get_or_create(code=code, defaults={'title': title})[0]
            for code, title in [
                ('available', 'Свободна'),
                ('bound', 'Привязана'),
                ('archived', 'Архивирована'),
            ]
        }
        move_event_types = {
            code: MoveEventType.objects.get_or_create(code=code, defaults={'title': title})[0]
            for code, title in [
                ('scan', 'Сканирование'),
                ('transfer', 'Передача'),
                ('waiting', 'Ожидание'),
                ('prep', 'Подготовка'),
            ]
        }
        move_sources = {
            code: MoveSource.objects.get_or_create(code=code, defaults={'title': title})[0]
            for code, title in [
                ('booktrail_route', 'Маршрут BookTrail'),
            ]
        }
        review_statuses = {
            code: ReviewModerationStatus.objects.get_or_create(code=code, defaults={'title': title})[0]
            for code, title in [
                ('published', 'Опубликован'),
                ('pending', 'На модерации'),
                ('rejected', 'Отклонён'),
            ]
        }
        notification_kinds = {
            code: NotificationKind.objects.get_or_create(code=code, defaults={'title': title})[0]
            for code, title in [
                ('move', 'Перемещение'),
                ('review', 'Отзыв'),
                ('recommendation', 'Рекомендация'),
                ('nfc', 'NFC'),
            ]
        }

        roles = {
            'member': Role.objects.get_or_create(code='member', defaults={'title': 'Участник'})[0],
            'moderator': Role.objects.get_or_create(code='moderator', defaults={'title': 'Модератор'})[0],
            'admin': Role.objects.get_or_create(code='admin', defaults={'title': 'Администратор'})[0],
        }

        users = [
            User.objects.get_or_create(
                username='reader',
                defaults={
                    'email': 'reader@booktrail.io',
                    'first_name': 'Алиса',
                    'last_name': 'Морозова',
                    'is_active': True,
                },
            )[0],
            User.objects.get_or_create(
                username='moderator',
                defaults={
                    'email': 'moderator@booktrail.io',
                    'first_name': 'Куратор',
                    'last_name': 'Ленты',
                    'is_active': True,
                },
            )[0],
            User.objects.get_or_create(
                username='admin',
                defaults={
                    'email': 'admin@booktrail.io',
                    'first_name': 'Админ',
                    'last_name': 'BookTrail',
                    'is_active': True,
                    'is_staff': True,
                },
            )[0],
        ]
        for user, is_staff, is_superuser in [
            (users[0], False, False),
            (users[1], False, False),
            (users[2], True, True),
        ]:
            user.set_password(DEMO_USER_PASSWORD)
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.is_active = True
            user.save(update_fields=['password', 'is_staff', 'is_superuser', 'is_active'])

        profile_defaults = [
            {'avatar': 'AB', 'status': 'Исследователь маршрутов', 'show_profile': True, 'share_reviews': True, 'nfc_visibility': False},
            {'avatar': 'KM', 'status': 'Модерация и события', 'show_profile': True, 'share_reviews': True, 'nfc_visibility': True},
            {'avatar': 'AD', 'status': 'Оператор платформы', 'show_profile': False, 'share_reviews': False, 'nfc_visibility': False},
        ]
        for user, defaults in zip(users, profile_defaults, strict=True):
            profile = ensure_profile(user)
            for field, value in defaults.items():
                setattr(profile, field, value)
            profile.save(update_fields=list(defaults.keys()) + ['updated_at'])

        UserRole.objects.get_or_create(user=users[0], role=roles['member'])
        UserRole.objects.get_or_create(user=users[1], role=roles['moderator'])
        UserRole.objects.get_or_create(user=users[2], role=roles['admin'])

        book_payloads = [
            {
                'title': 'Ночной архив',
                'authors': ['Мира Левина'],
                'genre': 'Киберпанк',
                'language': ('Русский', 'ru'),
                'year': 2023,
                'description': 'История о цифровых следах, памяти и людях, которые находят себя в маршрутах чужих книг.',
                'cover': 'web/img/placeholder-cover.svg',
                'accent': 'cyan',
            },
            {
                'title': 'Signal & Paper',
                'authors': ['Jonah Reed', 'Elena Park'],
                'genre': 'Non-fiction',
                'language': ('English', 'en'),
                'year': 2021,
                'description': 'A practical exploration of community reading trails, ambient tech, and how physical books create social graphs.',
                'cover': 'web/img/placeholder-cover.svg',
                'accent': 'magenta',
            },
            {
                'title': 'Карта тихих городов',
                'authors': ['Илья Руденко'],
                'genre': 'Современная проза',
                'language': ('Русский', 'ru'),
                'year': 2020,
                'description': 'Лиричный роман о людях, которые оставляют сообщения в книгах и меняют чужие маршруты.',
                'cover': 'web/img/placeholder-cover.svg',
                'accent': 'lime',
            },
            {
                'title': 'Neon Margins',
                'authors': ['Sofia Laurent'],
                'genre': 'Sci-fi',
                'language': ('English', 'en'),
                'year': 2024,
                'description': 'When books begin to report their journeys, readers discover a city hidden inside metadata.',
                'cover': 'web/img/placeholder-cover.svg',
                'accent': 'blue',
            },
            {
                'title': 'Тепловые карты чтения',
                'authors': ['Ольга Рябина'],
                'genre': 'Non-fiction',
                'language': ('Русский', 'ru'),
                'year': 2022,
                'description': 'Заметки о том, как привычки чтения складываются в карту города и обратно.',
                'cover': 'web/img/placeholder-cover.svg',
                'accent': 'cyan',
            },
            {
                'title': 'Paper Comets',
                'authors': ['M. Choi'],
                'genre': 'Fiction',
                'language': ('English', 'en'),
                'year': 2019,
                'description': 'Short stories about travelling books and the people who keep them moving.',
                'cover': 'web/img/placeholder-cover.svg',
                'accent': 'magenta',
            },
            {
                'title': 'Свет на корешке',
                'authors': ['Наталья Хромова'],
                'genre': 'Современная проза',
                'language': ('Русский', 'ru'),
                'year': 2021,
                'description': 'Небольшой роман о встречах, которые начинаются с найденной книги.',
                'cover': 'web/img/placeholder-cover.svg',
                'accent': 'lime',
            },
            {
                'title': 'The Quiet Shelf',
                'authors': ['A. Monroe'],
                'genre': 'Sci-fi',
                'language': ('English', 'en'),
                'year': 2020,
                'description': 'A near-future tale about libraries that talk to one another via NFC tags.',
                'cover': 'web/img/placeholder-cover.svg',
                'accent': 'blue',
            },
            {
                'title': 'Маршруты между строк',
                'authors': ['Глеб Соловьёв'],
                'genre': 'Non-fiction',
                'language': ('Русский', 'ru'),
                'year': 2023,
                'description': 'Практический гид по книжным тропам, встречам и заметкам на полях.',
                'cover': 'web/img/placeholder-cover.svg',
                'accent': 'cyan',
            },
            {
                'title': 'Afterword District',
                'authors': ['Leila Grant'],
                'genre': 'Fiction',
                'language': ('English', 'en'),
                'year': 2022,
                'description': 'A city where every book stores a short afterword from its last reader.',
                'cover': 'web/img/placeholder-cover.svg',
                'accent': 'magenta',
            },
        ]

        books: list[Book] = []
        for payload in book_payloads:
            genre, _ = Genre.objects.get_or_create(
                name=payload['genre'],
                defaults={'slug': slugify(payload['genre'], allow_unicode=True)},
            )
            language_name, language_code = payload['language']
            language, _ = Language.objects.get_or_create(name=language_name, defaults={'code': language_code})
            book, _ = Book.objects.get_or_create(
                title=payload['title'],
                defaults={
                    'genre': genre,
                    'language': language,
                    'year': payload['year'],
                    'description': payload['description'],
                    'cover': payload['cover'],
                    'accent': payload['accent'],
                },
            )
            book.genre = genre
            book.language = language
            book.year = payload['year']
            book.description = payload['description']
            book.cover = payload['cover']
            book.accent = payload['accent']
            book.save()

            for order, author_name in enumerate(payload['authors']):
                author, _ = Author.objects.get_or_create(name=author_name)
                BookAuthor.objects.get_or_create(book=book, author=author, defaults={'sort_order': order})

            books.append(book)

        copies: list[Copy] = []
        next_code_num = 1000
        copy_status_values = list(copy_statuses.values())
        for book in books:
            for _ in range(random.choice([1, 2, 2, 3])):
                next_code_num += 1
                code_prefix = slugify(book.title, allow_unicode=False).upper()[:3] or 'BK'
                code = f'BT-{code_prefix}-{next_code_num:04d}'
                copy, _ = Copy.objects.get_or_create(
                    code=code,
                    defaults={
                        'book': book,
                        'status': random.choice(copy_status_values),
                        'initiator': random.choice(users),
                    },
                )
                copies.append(copy)

        tags: list[NfcTag] = []
        for idx in range(max(10, min(20, len(copies)))):
            uid = f'NFC-{idx:04d}-{uuid.uuid4().hex[:4].upper()}'
            tag, _ = NfcTag.objects.get_or_create(uid=uid, defaults={'status': tag_statuses['bound']})
            tags.append(tag)

        random.shuffle(copies)
        random.shuffle(tags)
        copies_for_binds = copies[: max(8, len(copies) // 2)]
        for copy, tag in zip(copies_for_binds, tags, strict=False):
            TagBind.objects.get_or_create(
                copy=copy,
                tag=tag,
                ended_at=None,
                defaults={
                    'started_at': _dt(days_ago=random.randint(1, 30)),
                    'created_by': random.choice(users),
                },
            )
            tag.status = tag_statuses['bound']
            tag.save(update_fields=['status'])

        move_type_values = list(move_event_types.values())
        places = [
            'Коворкинг «Сигнал»',
            'Книжный клуб «Орбита»',
            'Кафе «Линия текста»',
            'Metro Library Point',
            'Полка обмена у входа',
            'Лекторий «Бук-спот»',
        ]
        move_texts = [
            'Экземпляр отметил новую точку маршрута.',
            'Книга нашла нового читателя.',
            'Книга переместилась на другую полку.',
            'Экземпляр ждёт привязки новой NFC-метки.',
        ]
        for copy in copies[: min(len(copies), 12)]:
            bind = TagBind.objects.filter(copy=copy, ended_at__isnull=True).select_related('tag').first()
            tag = bind.tag if bind else None
            events_count = random.randint(3, 8)
            for i in range(events_count):
                dt = _dt(days_ago=events_count - i, minutes_offset=random.randint(0, 720))
                event_type = random.choice(move_type_values)
                Move.objects.get_or_create(
                    copy=copy,
                    date_time=dt,
                    event_type=event_type,
                    defaults={
                        'user': random.choice(users),
                        'place_text': random.choice(places),
                        'text': random.choice(move_texts),
                        'payload': '' if event_type.code != 'scan' else '{"reader":"nfc"}',
                        'nfc_tag': tag,
                        'source': move_sources['booktrail_route'],
                    },
                )

        review_status_values = list(review_statuses.values())
        for book in books:
            for author in random.sample(users, k=random.randint(1, min(3, len(users)))):
                Review.objects.get_or_create(
                    book=book,
                    author=author,
                    defaults={
                        'rating': random.randint(3, 5),
                        'text': random.choice(
                            [
                                'Очень атмосферно, хочется продолжать маршрут.',
                                'Книга оставляет след и в голове, и в городе.',
                                'Интересно наблюдать, как текст переезжает между людьми.',
                                'Отличное чтение в дороге, заметки на полях радуют.',
                            ]
                        ),
                        'moderation_status': random.choice(review_status_values),
                    },
                )

        user = users[0]
        for book in random.sample(books, k=min(len(books), random.randint(10, 12))):
            Recommendation.objects.get_or_create(
                user=user,
                book=book,
                defaults={
                    'score': round(random.uniform(0.72, 0.99), 4),
                    'explanation': random.choice(
                        [
                            'Похоже по маршрутам и темам отзывов.',
                            'Совпадает язык и настроение ленты событий.',
                            'Часто встречается в тех же точках обмена.',
                            'Похожий жанр и высокий рейтинг у читателей.',
                        ]
                    ),
                },
            )

        notification_kind_values = list(notification_kinds.values())
        for _ in range(random.randint(8, 15)):
            Notification.objects.get_or_create(
                user=user,
                title=random.choice(['Новый читатель', 'Сканирование', 'Отзыв', 'Рекомендация обновлена']),
                text=random.choice(
                    [
                        'Ваш экземпляр отметил новую точку маршрута.',
                        'Появился новый отзыв на книгу из вашего маршрута.',
                        'Рекомендации обновлены после новых событий.',
                        'Метка успешно привязана к экземпляру.',
                    ]
                ),
                kind=random.choice(notification_kind_values),
                defaults={'is_read': random.random() < 0.35},
            )

        session_payloads = [
            {'device': 'Chrome · macOS', 'location': 'Санкт-Петербург', 'minutes': 40, 'current': True},
            {'device': 'Safari · iPhone', 'location': 'Таллин', 'minutes': 60 * 12, 'current': False},
            {'device': 'Firefox · Windows', 'location': 'Москва', 'minutes': 60 * 36, 'current': False},
        ]
        target_sessions = random.randint(1, 3)
        for payload in session_payloads[:target_sessions]:
            AuthSession.objects.get_or_create(
                user=user,
                device=payload['device'],
                location=payload['location'],
                defaults={
                    'last_seen': timezone.now() - timedelta(minutes=payload['minutes']),
                    'refresh_token_hash': str(uuid.uuid4()),
                    'revoked': False,
                    'current': payload['current'],
                },
            )

        self.stdout.write(self.style.SUCCESS('Seed completed.'))
