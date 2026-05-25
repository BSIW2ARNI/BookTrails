from __future__ import annotations

from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
import json

from .models import (
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
    TagBind,
)
from .recommendation_engine import generate_recommendations_for_user, persist_recommendations_for_user
from .utils import ensure_profile


class BookTrailBaseTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.copy_status = CopyStatus.objects.get_or_create(code='waiting', defaults={'title': 'Ожидает следующего читателя'})[0]
        cls.tag_available = NfcTagStatus.objects.get_or_create(code='available', defaults={'title': 'Свободна'})[0]
        cls.tag_bound = NfcTagStatus.objects.get_or_create(code='bound', defaults={'title': 'Привязана'})[0]
        cls.tag_archived = NfcTagStatus.objects.get_or_create(code='archived', defaults={'title': 'Архивирована'})[0]
        cls.event_scan = MoveEventType.objects.get_or_create(code='scan', defaults={'title': 'Сканирование'})[0]
        cls.event_transfer = MoveEventType.objects.get_or_create(code='transfer', defaults={'title': 'Передача'})[0]
        cls.move_source = MoveSource.objects.get_or_create(code='booktrail_route', defaults={'title': 'Маршрут BookTrail'})[0]
        cls.review_status = ReviewModerationStatus.objects.get_or_create(code='published', defaults={'title': 'Опубликован'})[0]
        cls.notification_kind = NotificationKind.objects.get_or_create(code='move', defaults={'title': 'Перемещение'})[0]

        cls.genre = Genre.objects.get_or_create(name='Фантастика', defaults={'slug': 'fantasy'})[0]
        cls.language = Language.objects.get_or_create(name='Русский', defaults={'code': 'ru-test'})[0]
        cls.author = Author.objects.get_or_create(name='Тестовый Автор')[0]
        cls.book = Book.objects.create(
            title='Тестовая книга',
            genre=cls.genre,
            language=cls.language,
            year=2024,
            description='Описание для тестов.',
            isbn='978-5-0000-0001-1',
        )
        BookAuthor.objects.get_or_create(book=cls.book, author=cls.author, defaults={'sort_order': 0})

        cls.user = User.objects.create_user(
            username='reader-test@example.com',
            email='reader-test@example.com',
            password='StrongPass123',
            first_name='Reader',
            last_name='User',
        )
        cls.other_user = User.objects.create_user(
            username='other-test@example.com',
            email='other-test@example.com',
            password='StrongPass123',
            first_name='Other',
            last_name='User',
        )
        cls.admin_user = User.objects.create_user(
            username='admin-test@example.com',
            email='admin-test@example.com',
            password='StrongPass123',
            first_name='Admin',
            last_name='User',
            is_staff=True,
            is_superuser=True,
        )
        ensure_profile(cls.user)
        ensure_profile(cls.other_user)
        ensure_profile(cls.admin_user)

        cls.copy = Copy.objects.create(book=cls.book, code='BT-001', status=cls.copy_status, initiator=cls.user)
        cls.other_copy = Copy.objects.create(book=cls.book, code='BT-002', status=cls.copy_status, initiator=cls.other_user)

        cls.notification = Notification.objects.create(
            user=cls.user,
            title='Новое событие',
            text='Книга продолжила маршрут.',
            kind=cls.notification_kind,
        )
        cls.other_notification = Notification.objects.create(
            user=cls.other_user,
            title='Чужое уведомление',
            text='Не должно быть доступно.',
            kind=cls.notification_kind,
        )
        Recommendation.objects.create(user=cls.user, book=cls.book, score=0.98, explanation='Подходит по жанру.')


class ModelValidationTests(BookTrailBaseTestCase):
    def test_review_rating_must_be_between_one_and_five(self):
        review = Review(
            book=self.book,
            author=self.user,
            rating=6,
            text='Некорректный отзыв',
            moderation_status=self.review_status,
        )

        with self.assertRaises(ValidationError):
            review.full_clean()

        with self.assertRaises(ValidationError):
            review.save()

    def test_tag_bind_rejects_archived_tag(self):
        tag = NfcTag.objects.create(uid='ARCHIVED-1', status=self.tag_archived)
        bind = TagBind(
            copy=self.copy,
            tag=tag,
            started_at=timezone.now(),
            created_by=self.user,
        )

        with self.assertRaises(ValidationError):
            bind.save()

    def test_tag_bind_rejects_active_tag_on_other_copy(self):
        tag = NfcTag.objects.create(uid='TAG-001', status=self.tag_available)
        TagBind.objects.create(copy=self.copy, tag=tag, started_at=timezone.now(), created_by=self.user)

        second_bind = TagBind(
            copy=self.other_copy,
            tag=tag,
            started_at=timezone.now() + timedelta(minutes=1),
            created_by=self.other_user,
        )

        with self.assertRaises(ValidationError):
            second_bind.save()

    def test_tag_bind_rejects_end_before_start(self):
        tag = NfcTag.objects.create(uid='TAG-002', status=self.tag_available)
        bind = TagBind(
            copy=self.copy,
            tag=tag,
            started_at=timezone.now(),
            ended_at=timezone.now() - timedelta(minutes=5),
            created_by=self.user,
        )

        with self.assertRaises(ValidationError):
            bind.full_clean()

    def test_move_rejects_tag_bound_to_other_copy(self):
        tag = NfcTag.objects.create(uid='TAG-003', status=self.tag_available)
        TagBind.objects.create(copy=self.other_copy, tag=tag, started_at=timezone.now(), created_by=self.other_user)

        move = Move(
            copy=self.copy,
            user=self.user,
            event_type=self.event_transfer,
            date_time=timezone.now(),
            place_text='Полка',
            text='Неверный тэг',
            source=self.move_source,
            nfc_tag=tag,
        )

        with self.assertRaises(ValidationError):
            move.save()

    def test_review_rating_db_constraint_exists(self):
        with self.assertRaises(IntegrityError):
            Review.objects.bulk_create(
                [
                    Review(
                        book=self.book,
                        author=self.user,
                        rating=0,
                        text='invalid',
                        moderation_status=self.review_status,
                    )
                ]
            )


class AuthAndP1FlowTests(BookTrailBaseTestCase):
    def setUp(self):
        self.client = Client()

    def test_private_pages_require_login(self):
        private_urls = [
            reverse('web:profile'),
            reverse('web:notifications'),
            reverse('web:recommendations'),
            reverse('web:scan'),
        ]

        for url in private_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse('web:auth_login'), response.url)

    def test_register_login_logout_flow(self):
        response = self.client.post(
            reverse('web:auth_register'),
            {
                'full_name': 'New Reader',
                'email': 'new.reader@example.com',
                'password1': 'StrongPass123',
                'password2': 'StrongPass123',
            },
        )
        self.assertRedirects(response, reverse('web:profile'))
        self.assertTrue(User.objects.filter(username='new.reader@example.com').exists())

        logout_response = self.client.post(reverse('web:auth_logout'))
        self.assertRedirects(logout_response, reverse('web:landing'))

        login_response = self.client.post(
            reverse('web:auth_login'),
            {'login': 'new.reader@example.com', 'password': 'StrongPass123'},
        )
        self.assertRedirects(login_response, reverse('web:profile'))


class RecommendationEngineTests(BookTrailBaseTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.genre_alt = Genre.objects.get_or_create(name='Детектив', defaults={'slug': 'detective'})[0]
        cls.author_alt = Author.objects.get_or_create(name='Второй Автор')[0]

        cls.similar_book = Book.objects.create(
            title='Тестовая книга 2',
            genre=cls.genre,
            language=cls.language,
            year=2025,
            description='Описание для тестов про фантастику, маршрут книги и читателей.',
            isbn='978-5-0000-0001-2',
        )
        BookAuthor.objects.get_or_create(book=cls.similar_book, author=cls.author, defaults={'sort_order': 0})

        cls.different_book = Book.objects.create(
            title='Совсем другая книга',
            genre=cls.genre_alt,
            language=cls.language,
            year=2022,
            description='Детективная история о расследовании и пропавших уликах.',
            isbn='978-5-0000-0001-3',
        )
        BookAuthor.objects.get_or_create(book=cls.different_book, author=cls.author_alt, defaults={'sort_order': 0})

        Review.objects.create(
            book=cls.book,
            author=cls.user,
            rating=5,
            text='Очень понравилась фантастика, маршрут книги и атмосфера сообщества.',
            moderation_status=cls.review_status,
        )
        Review.objects.create(
            book=cls.similar_book,
            author=cls.other_user,
            rating=5,
            text='Похожая фантастика, читатели и маршрут книги.',
            moderation_status=cls.review_status,
        )
        Review.objects.create(
            book=cls.different_book,
            author=cls.other_user,
            rating=3,
            text='Обычный детектив без книжного маршрута.',
            moderation_status=cls.review_status,
        )

    def test_generate_recommendations_prefers_semantically_similar_book(self):
        recommendations = generate_recommendations_for_user(self.user, limit=5)
        self.assertTrue(recommendations)
        self.assertEqual(recommendations[0]['book'].id, self.similar_book.id)

    def test_persist_recommendations_replaces_old_entries(self):
        Recommendation.objects.create(
            user=self.user,
            book=self.different_book,
            score=0.10,
            explanation='Старая рекомендация.',
        )

        created = persist_recommendations_for_user(self.user, limit=5)
        self.assertTrue(created)
        self.assertEqual(Recommendation.objects.filter(user=self.user).count(), len(created))
        self.assertFalse(
            Recommendation.objects.filter(
                user=self.user,
                book=self.different_book,
                explanation='Старая рекомендация.',
            ).exists()
        )

    def test_generate_recommendations_falls_back_to_popular_books_without_history(self):
        fresh_user = User.objects.create_user(
            username='fresh@example.com',
            email='fresh@example.com',
            password='StrongPass123',
        )
        ensure_profile(fresh_user)

        recommendations = generate_recommendations_for_user(fresh_user, limit=3)
        self.assertTrue(recommendations)
        self.assertIn('популярности', recommendations[0]['explanation'])

    def test_profile_update_updates_user_and_profile(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('web:profile'),
            {
                'full_name': 'Updated Reader',
                'email': 'updated.reader@example.com',
                'avatar': 'ur',
                'status': 'В пути',
                'show_profile': 'on',
                'share_reviews': '',
                'nfc_visibility': 'on',
            },
        )
        self.assertRedirects(response, reverse('web:profile'))

        self.user.refresh_from_db()
        profile = self.user.booktrail_profile
        profile.refresh_from_db()

        self.assertEqual(self.user.username, 'updated.reader@example.com')
        self.assertEqual(self.user.email, 'updated.reader@example.com')
        self.assertEqual(self.user.get_full_name(), 'Updated Reader')
        self.assertEqual(profile.avatar, 'UR')
        self.assertEqual(profile.status, 'В пути')
        self.assertTrue(profile.show_profile)
        self.assertFalse(profile.share_reviews)
        self.assertTrue(profile.nfc_visibility)

    def test_review_crud_flow(self):
        self.client.force_login(self.user)

        save_response = self.client.post(
            reverse('web:book_detail', args=[self.book.id]),
            {'action': 'save_review', 'rating': '5', 'text': 'Отзыв из теста'},
        )
        self.assertRedirects(save_response, f"{reverse('web:book_detail', args=[self.book.id])}#reviews")

        review = Review.objects.get(book=self.book, author=self.user)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.text, 'Отзыв из теста')

        delete_response = self.client.post(
            reverse('web:book_detail', args=[self.book.id]),
            {'action': 'delete_review'},
        )
        self.assertRedirects(delete_response, f"{reverse('web:book_detail', args=[self.book.id])}#reviews")
        self.assertFalse(Review.objects.filter(book=self.book, author=self.user).exists())

    def test_catalog_search_finds_by_author_and_isbn(self):
        self.client.force_login(self.user)

        author_response = self.client.get(reverse('web:catalog'), {'q': 'Тестовый Автор'})
        self.assertContains(author_response, self.book.title)

        isbn_response = self.client.get(reverse('web:catalog'), {'q': self.book.isbn})
        self.assertContains(isbn_response, self.book.title)

    def test_notifications_mark_read_and_foreign_notification_forbidden(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('web:notifications'),
            {'action': 'mark_read', 'notification_id': self.notification.id},
        )
        self.assertRedirects(response, reverse('web:notifications'))
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

        foreign_response = self.client.post(
            reverse('web:notifications'),
            {'action': 'mark_read', 'notification_id': self.other_notification.id},
        )
        self.assertEqual(foreign_response.status_code, 404)

    def test_copy_actions_and_scan_flow(self):
        self.client.force_login(self.user)

        move_response = self.client.post(
            reverse('web:copy_detail', args=[self.copy.id]),
            {
                'action': 'add_move',
                'event_type': str(self.event_transfer.id),
                'place_text': 'Новая точка',
                'text': 'Книга передана дальше',
            },
        )
        self.assertRedirects(move_response, f"{reverse('web:copy_detail', args=[self.copy.id])}#copy-actions")
        self.assertTrue(Move.objects.filter(copy=self.copy, user=self.user, text='Книга передана дальше').exists())

        bind_response = self.client.post(
            reverse('web:copy_detail', args=[self.copy.id]),
            {
                'action': 'bind_tag',
                'tag_uid': 'FLOW-TAG-001',
            },
        )
        self.assertRedirects(bind_response, f"{reverse('web:copy_detail', args=[self.copy.id])}#copy-actions")
        active_bind = TagBind.objects.get(copy=self.copy, ended_at__isnull=True)
        self.assertEqual(active_bind.tag.uid, 'FLOW-TAG-001')
        self.assertEqual(active_bind.tag.status.code, 'bound')

        scan_response = self.client.post(
            reverse('web:scan'),
            {
                'tag_uid': 'FLOW-TAG-001',
                'copy_code': '',
                'place_text': 'Полка сообщества',
                'text': 'Сканирование из теста',
            },
        )
        self.assertRedirects(scan_response, reverse('web:scan'))
        self.assertTrue(
            Move.objects.filter(
                copy=self.copy,
                user=self.user,
                event_type=self.event_scan,
                text='Сканирование из теста',
            ).exists()
        )

        unbind_response = self.client.post(
            reverse('web:copy_detail', args=[self.copy.id]),
            {'action': 'unbind_tag'},
        )
        self.assertRedirects(unbind_response, f"{reverse('web:copy_detail', args=[self.copy.id])}#copy-actions")
        active_bind.refresh_from_db()
        active_bind.tag.refresh_from_db()
        self.assertIsNotNone(active_bind.ended_at)
        self.assertEqual(active_bind.tag.status.code, 'available')


class MobileApiTests(BookTrailBaseTestCase):
    def setUp(self):
        self.client = Client()

    def _register_and_get_tokens(self):
        response = self.client.post(
            '/api/v1/auth/register',
            data=json.dumps(
                {
                    'full_name': 'API Reader',
                    'email': 'api.reader@example.com',
                    'password': 'StrongPass123',
                    'password_confirmation': 'StrongPass123',
                }
            ),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        return body['access'], body['refresh']

    def test_api_register_login_refresh_logout_and_me(self):
        access, refresh = self._register_and_get_tokens()

        me_response = self.client.get('/api/v1/me', HTTP_AUTHORIZATION=f'Bearer {access}')
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.json()['email'], 'api.reader@example.com')

        refresh_response = self.client.post(
            '/api/v1/auth/refresh',
            data=json.dumps({'refresh': refresh}),
            content_type='application/json',
        )
        self.assertEqual(refresh_response.status_code, 200)
        self.assertIn('access', refresh_response.json())

        logout_response = self.client.post(
            '/api/v1/auth/logout',
            data=json.dumps({'refresh': refresh}),
            content_type='application/json',
        )
        self.assertEqual(logout_response.status_code, 204)

        refresh_after_logout = self.client.post(
            '/api/v1/auth/refresh',
            data=json.dumps({'refresh': refresh}),
            content_type='application/json',
        )
        self.assertEqual(refresh_after_logout.status_code, 401)

        login_response = self.client.post(
            '/api/v1/auth/login',
            data=json.dumps(
                {
                    'login': 'api.reader@example.com',
                    'password': 'StrongPass123',
                    'device': 'Pixel',
                    'platform': 'android',
                }
            ),
            content_type='application/json',
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertIn('access', login_response.json())

    def test_api_read_only_endpoints(self):
        self.client.force_login(self.user)
        review = Review.objects.create(
            book=self.book,
            author=self.user,
            rating=5,
            text='API отзыв',
            moderation_status=self.review_status,
        )
        Move.objects.create(
            copy=self.copy,
            user=self.user,
            event_type=self.event_transfer,
            date_time=timezone.now(),
            place_text='Полка API',
            text='Маршрут через API',
            source=self.move_source,
        )

        login_response = self.client.post(
            '/api/v1/auth/login',
            data=json.dumps({'login': self.user.email, 'password': 'StrongPass123'}),
            content_type='application/json',
        )
        access = login_response.json()['access']

        books_response = self.client.get('/api/v1/books?q=Тестовая', HTTP_AUTHORIZATION=f'Bearer {access}')
        self.assertEqual(books_response.status_code, 200)
        self.assertEqual(books_response.json()['items'][0]['title'], self.book.title)

        book_response = self.client.get(f'/api/v1/books/{self.book.id}', HTTP_AUTHORIZATION=f'Bearer {access}')
        self.assertEqual(book_response.status_code, 200)
        self.assertEqual(book_response.json()['user_review']['id'], review.id)

        with_reader_status = CopyStatus.objects.get_or_create(code='with_reader', defaults={'title': 'У читателя'})[0]
        self.copy.status = with_reader_status
        self.copy.holder = self.user
        self.copy.save(update_fields=['status', 'holder'])
        copy_response = self.client.get(f'/api/v1/copies/{self.copy.id}', HTTP_AUTHORIZATION=f'Bearer {access}')
        self.assertEqual(copy_response.status_code, 200)
        self.assertEqual(copy_response.json()['code'], self.copy.code)
        self.assertEqual(copy_response.json()['presence']['holder']['email'], self.user.email)
        self.assertTrue(copy_response.json()['presence']['held_by_current_user'])

        events_response = self.client.get('/api/v1/events', HTTP_AUTHORIZATION=f'Bearer {access}')
        self.assertEqual(events_response.status_code, 200)
        self.assertGreaterEqual(len(events_response.json()['items']), 1)

        notifications_response = self.client.get('/api/v1/notifications', HTTP_AUTHORIZATION=f'Bearer {access}')
        self.assertEqual(notifications_response.status_code, 200)
        self.assertEqual(notifications_response.json()['items'][0]['title'], self.notification.title)

        recommendations_response = self.client.get('/api/v1/recommendations', HTTP_AUTHORIZATION=f'Bearer {access}')
        self.assertEqual(recommendations_response.status_code, 200)
        self.assertEqual(recommendations_response.json()['items'][0]['book_id'], self.book.id)

    def test_api_write_endpoints(self):
        login_response = self.client.post(
            '/api/v1/auth/login',
            data=json.dumps({'login': self.user.email, 'password': 'StrongPass123'}),
            content_type='application/json',
        )
        access = login_response.json()['access']

        me_patch = self.client.patch(
            '/api/v1/me',
            data=json.dumps(
                {
                    'full_name': 'Updated Mobile User',
                    'email': 'reader-test@example.com',
                    'avatar': 'um',
                    'status': 'В движении',
                    'privacy': {
                        'show_profile': True,
                        'share_reviews': False,
                        'nfc_visibility': True,
                    },
                }
            ),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {access}',
        )
        self.assertEqual(me_patch.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.get_full_name(), 'Updated Mobile User')
        self.assertEqual(self.user.booktrail_profile.avatar, 'UM')

        review_create = self.client.post(
            f'/api/v1/books/{self.book.id}/reviews',
            data=json.dumps({'rating': 5, 'text': 'Mobile review'}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {access}',
        )
        self.assertIn(review_create.status_code, {200, 201})
        review_id = review_create.json()['id']

        review_update = self.client.patch(
            f'/api/v1/reviews/{review_id}',
            data=json.dumps({'rating': 4, 'text': 'Updated mobile review'}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {access}',
        )
        self.assertEqual(review_update.status_code, 200)
        self.assertEqual(review_update.json()['rating'], 4)

        bind_tag = self.client.post(
            f'/api/v1/copies/{self.copy.id}/bind-tag',
            data=json.dumps({'tag_uid': 'API-TAG-001'}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {access}',
        )
        self.assertEqual(bind_tag.status_code, 200)

        move_create = self.client.post(
            f'/api/v1/copies/{self.copy.id}/moves',
            data=json.dumps({'event_type_code': 'transfer', 'place_text': 'API shelf', 'text': 'Move from API'}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {access}',
        )
        self.assertEqual(move_create.status_code, 201)

        scan_create = self.client.post(
            '/api/v1/scan',
            data=json.dumps({'tag_uid': 'API-TAG-001', 'place_text': 'Scan point', 'text': 'Scanned via API'}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {access}',
        )
        self.assertEqual(scan_create.status_code, 201)
        self.copy.refresh_from_db()
        self.assertEqual(self.copy.status.code, 'with_reader')
        self.assertEqual(self.copy.holder_id, self.user.id)

        admin_login = self.client.post(
            '/api/v1/auth/login',
            data=json.dumps({'login': self.admin_user.email, 'password': 'StrongPass123'}),
            content_type='application/json',
        )
        admin_access = admin_login.json()['access']
        waiting_status = CopyStatus.objects.get_or_create(code='waiting', defaults={'title': 'Ожидает следующего читателя'})[0]
        update_status = self.client.patch(
            f'/api/v1/copies/{self.copy.id}',
            data=json.dumps({'status_code': waiting_status.code, 'note': 'Возврат на полку'}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {admin_access}',
        )
        self.assertEqual(update_status.status_code, 200)
        self.copy.refresh_from_db()
        self.assertEqual(self.copy.status.code, waiting_status.code)
        self.assertIsNone(self.copy.holder)

        mark_read = self.client.post(
            f'/api/v1/notifications/{self.notification.id}/mark-read',
            data=json.dumps({}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {access}',
        )
        self.assertEqual(mark_read.status_code, 200)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

        Notification.objects.create(
            user=self.user,
            title='Еще одно уведомление',
            text='Непрочитанное',
            kind=self.notification_kind,
        )
        mark_all = self.client.post(
            '/api/v1/notifications/mark-all-read',
            data=json.dumps({}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {access}',
        )
        self.assertEqual(mark_all.status_code, 200)
        self.assertGreaterEqual(mark_all.json()['updated'], 1)

        unbind_tag = self.client.post(
            f'/api/v1/copies/{self.copy.id}/unbind-tag',
            data=json.dumps({}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {access}',
        )
        self.assertEqual(unbind_tag.status_code, 200)

        review_delete = self.client.delete(
            f'/api/v1/reviews/{review_id}',
            HTTP_AUTHORIZATION=f'Bearer {access}',
        )
        self.assertEqual(review_delete.status_code, 204)
