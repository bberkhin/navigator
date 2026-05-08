from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

# SQLite для локальной разработки
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Ключ-заглушка если .env не создан
import os
if not os.environ.get('SECRET_KEY'):
    SECRET_KEY = 'django-insecure-dev-only-change-before-deploy'
