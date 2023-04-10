import os
# from pathlib import Path


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'django-insecure-qw0vbkqjl8li8b!rq+^0b=n0bxhy@^oh17d^pve6x#4rxij0jz'

DEBUG = False

ALLOWED_HOSTS = ['*']

AUTH_USER_MODEL = 'core.Client'

ROOT_URLCONF = '_project_.urls'

WSGI_APPLICATION = '_project_.wsgi.application'

ASGI_APPLICATION = "_project_.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        }
    }
}

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATIC_ROOT = os.path.join(BASE_DIR, '..', 'static')
STATIC_URL = '/static/'

APPLICATION_FRONT_URL = ''
BACKEND_URL = ''
PAYMENT_LOGIN = ''
PAYMENT_PASSWORD = ''


if not DEBUG:
    import sentry_sdk
    sentry_sdk.init(
        dsn="https://5dd7154211b84e5ca1460e9d94b091ec@o1232908.ingest.sentry.io/4504474762412032",

        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0
    )

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.mail.ru'
EMAIL_PORT = 465
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''

SUPPORT_TG_BOT = ''
