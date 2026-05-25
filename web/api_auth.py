from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.utils import timezone as django_timezone

from .models import AuthSession
from .utils import ensure_profile


ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)
REFRESH_TOKEN_LIFETIME = timedelta(days=30)


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b'=').decode('ascii')


def _b64url_decode(value: str) -> bytes:
    padding = '=' * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode('ascii'))


def _jwt_secret() -> bytes:
    return settings.SECRET_KEY.encode('utf-8')


def _json_dumps(payload: dict) -> bytes:
    return json.dumps(payload, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def _sign(header_b64: str, payload_b64: str) -> str:
    data = f'{header_b64}.{payload_b64}'.encode('ascii')
    signature = hmac.new(_jwt_secret(), data, hashlib.sha256).digest()
    return _b64url_encode(signature)


def _token_expiry(lifetime: timedelta) -> int:
    return int((datetime.now(timezone.utc) + lifetime).timestamp())


def encode_jwt(payload: dict) -> str:
    header = {'alg': 'HS256', 'typ': 'JWT'}
    header_b64 = _b64url_encode(_json_dumps(header))
    payload_b64 = _b64url_encode(_json_dumps(payload))
    signature_b64 = _sign(header_b64, payload_b64)
    return f'{header_b64}.{payload_b64}.{signature_b64}'


def decode_jwt(token: str) -> dict:
    try:
        header_b64, payload_b64, signature_b64 = token.split('.')
    except ValueError as error:
        raise PermissionDenied('Недействительный токен.') from error

    expected_signature = _sign(header_b64, payload_b64)
    if not hmac.compare_digest(signature_b64, expected_signature):
        raise PermissionDenied('Недействительный токен.')

    try:
        payload = json.loads(_b64url_decode(payload_b64).decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise PermissionDenied('Недействительный токен.') from error

    exp = payload.get('exp')
    if not isinstance(exp, int) or exp < int(datetime.now(timezone.utc).timestamp()):
        raise PermissionDenied('Срок действия токена истёк.')

    return payload


def hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()


def _access_payload(*, user: User, session: AuthSession) -> dict:
    return {
        'sub': user.id,
        'sid': session.id,
        'type': 'access',
        'exp': _token_expiry(ACCESS_TOKEN_LIFETIME),
    }


def _refresh_payload(*, user: User, session: AuthSession, token_id: str) -> dict:
    return {
        'sub': user.id,
        'sid': session.id,
        'jti': token_id,
        'type': 'refresh',
        'exp': _token_expiry(REFRESH_TOKEN_LIFETIME),
    }


def create_auth_session(user: User, *, device: str = '', location: str = '') -> tuple[str, str, AuthSession]:
    AuthSession.objects.filter(user=user, current=True).update(current=False)
    token_id = secrets.token_hex(16)
    session = AuthSession.objects.create(
        user=user,
        device=device[:120],
        location=location[:120],
        last_seen=django_timezone.now(),
        refresh_token_hash='pending',
        current=True,
        revoked=False,
    )
    refresh_token = encode_jwt(_refresh_payload(user=user, session=session, token_id=token_id))
    session.refresh_token_hash = hash_refresh_token(refresh_token)
    session.save(update_fields=['refresh_token_hash'])
    access_token = encode_jwt(_access_payload(user=user, session=session))
    ensure_profile(user)
    return access_token, refresh_token, session


def refresh_access_token(refresh_token: str) -> tuple[str, AuthSession]:
    payload = decode_jwt(refresh_token)
    if payload.get('type') != 'refresh':
        raise PermissionDenied('Ожидался refresh token.')

    session = (
        AuthSession.objects.select_related('user')
        .filter(id=payload.get('sid'), user_id=payload.get('sub'), revoked=False)
        .first()
    )
    if session is None:
        raise PermissionDenied('Сессия не найдена или отозвана.')

    if session.refresh_token_hash != hash_refresh_token(refresh_token):
        raise PermissionDenied('Refresh token недействителен.')

    session.last_seen = django_timezone.now()
    session.current = True
    session.save(update_fields=['last_seen', 'current'])
    access_token = encode_jwt(_access_payload(user=session.user, session=session))
    return access_token, session


def revoke_session_by_refresh_token(refresh_token: str) -> None:
    payload = decode_jwt(refresh_token)
    if payload.get('type') != 'refresh':
        raise PermissionDenied('Ожидался refresh token.')

    session = (
        AuthSession.objects.filter(id=payload.get('sid'), user_id=payload.get('sub'), revoked=False)
        .first()
    )
    if session is None:
        return

    if session.refresh_token_hash != hash_refresh_token(refresh_token):
        raise PermissionDenied('Refresh token недействителен.')

    session.revoked = True
    session.current = False
    session.last_seen = django_timezone.now()
    session.save(update_fields=['revoked', 'current', 'last_seen'])


def authenticate_access_token(authorization_header: str | None) -> tuple[User, AuthSession]:
    if not authorization_header:
        raise PermissionDenied('Требуется access token.')

    scheme, _, token = authorization_header.partition(' ')
    if scheme.lower() != 'bearer' or not token:
        raise PermissionDenied('Некорректный заголовок Authorization.')

    payload = decode_jwt(token)
    if payload.get('type') != 'access':
        raise PermissionDenied('Ожидался access token.')

    session = (
        AuthSession.objects.select_related('user')
        .filter(id=payload.get('sid'), user_id=payload.get('sub'), revoked=False)
        .first()
    )
    if session is None:
        raise PermissionDenied('Сессия не найдена или отозвана.')

    session.last_seen = django_timezone.now()
    session.current = True
    session.save(update_fields=['last_seen', 'current'])

    ensure_profile(session.user)
    return session.user, session
