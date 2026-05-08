from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Загрузка .env если есть python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass

SECRET_KEY = os.environ['SECRET_KEY']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.catalog',
    'apps.navigator',
    'apps.library',
    'apps.consult',
    'apps.cms',
    'apps.ai',
    'apps.map',
    'apps.accounts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Asia/Novosibirsk'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Ключи внешних сервисов — берутся из .env
TWOGIS_API_KEY = os.environ.get('TWOGIS_API_KEY', '')
GIGACHAT_CLIENT_ID = os.environ.get('GIGACHAT_CLIENT_ID', '')
GIGACHAT_AUTH_KEY = os.environ.get('GIGACHAT_AUTH_KEY', '')
GIGACHAT_SCOPE = os.environ.get('GIGACHAT_SCOPE', 'GIGACHAT_API_PERS')
VK_CLIENT_ID = os.environ.get('VK_CLIENT_ID', '')
VK_CLIENT_SECRET = os.environ.get('VK_CLIENT_SECRET', '')
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
GIT_AUTHOR_NAME = os.environ.get('GIT_AUTHOR_NAME', '')
GIT_AUTHOR_EMAIL = os.environ.get('GIT_AUTHOR_EMAIL', '')
