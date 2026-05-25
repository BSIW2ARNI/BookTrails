from __future__ import annotations

from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User

from .models import UserProfile


def ensure_profile(user: User) -> UserProfile:
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'avatar': (user.first_name[:1] + user.last_name[:1]).upper()[:2] or user.username[:2].upper(),
            'status': 'Исследователь маршрутов',
            'show_profile': True,
            'share_reviews': True,
            'nfc_visibility': False,
        },
    )
    return profile


def get_current_user(request) -> User:
    if not request.user.is_authenticated:
        raise PermissionDenied('Authentication required.')

    ensure_profile(request.user)
    return request.user
