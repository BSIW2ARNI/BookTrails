from .base import *  # noqa: F401,F403


DEBUG = env_bool('DJANGO_DEBUG', True)
ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS', ['127.0.0.1', 'localhost', 'testserver', '10.0.2.2'])

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
