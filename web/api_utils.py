from __future__ import annotations

import json
from functools import wraps

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt


def api_success(data=None, *, status: int = 200):
    if data is None:
        return JsonResponse({}, status=status)
    return JsonResponse(data, status=status)


def api_error(code: str, message: str, *, status: int, details: dict | None = None):
    payload = {
        'error': {
            'code': code,
            'message': message,
        }
    }
    if details:
        payload['error']['details'] = details
    return JsonResponse(payload, status=status)


def parse_json_body(request: HttpRequest) -> dict:
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ValueError('Invalid JSON body.')


def api_view(methods: list[str]):
    allowed_methods = {method.upper() for method in methods}

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            if request.method.upper() not in allowed_methods:
                return api_error('method_not_allowed', 'Метод не поддерживается.', status=405)

            try:
                return view_func(request, *args, **kwargs)
            except ValueError as error:
                return api_error('bad_request', str(error) or 'Некорректный запрос.', status=400)
            except PermissionDenied as error:
                return api_error('forbidden', str(error) or 'Доступ запрещён.', status=403)

        return csrf_exempt(wrapper)

    return decorator
