from django.urls import path

from . import api_views

urlpatterns = [
    path('auth/register', api_views.api_register, name='api_register'),
    path('auth/login', api_views.api_login, name='api_login'),
    path('auth/refresh', api_views.api_refresh, name='api_refresh'),
    path('auth/logout', api_views.api_logout, name='api_logout'),
    path('me', api_views.api_me, name='api_me'),
    path('books', api_views.api_books, name='api_books'),
    path('books/<int:id>', api_views.api_book_detail, name='api_book_detail'),
    path('books/<int:id>/reviews', api_views.api_book_review_create, name='api_book_review_create'),
    path('reviews/<int:id>', api_views.api_review_update, name='api_review_update'),
    path('copies/<int:id>', api_views.api_copy_detail, name='api_copy_detail'),
    path('copies/<int:id>/moves', api_views.api_copy_move_create, name='api_copy_move_create'),
    path('copies/<int:id>/bind-tag', api_views.api_copy_bind_tag, name='api_copy_bind_tag'),
    path('copies/<int:id>/unbind-tag', api_views.api_copy_unbind_tag, name='api_copy_unbind_tag'),
    path('events', api_views.api_events, name='api_events'),
    path('recommendations', api_views.api_recommendations, name='api_recommendations'),
    path('notifications', api_views.api_notifications, name='api_notifications'),
    path('notifications/mark-all-read', api_views.api_notifications_mark_all_read, name='api_notifications_mark_all_read'),
    path('notifications/<int:id>/mark-read', api_views.api_notification_mark_read, name='api_notification_mark_read'),
    path('scan', api_views.api_scan, name='api_scan'),
]
