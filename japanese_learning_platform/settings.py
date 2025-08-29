# Jazzmin custom menu order
from .jazzmin_settings import JAZZMIN_SETTINGS
"""
Cấu hình cơ bản cho dự án Django.
Các cài đặt chung cho cả môi trường phát triển và sản xuất.
"""

import os
from pathlib import Path
from decouple import config
from dotenv import load_dotenv
load_dotenv(os.path.join(Path(__file__).resolve().parent.parent, '.env'))
from constants import (
    MIN_PASSWORD_LENGTH,
    SESSION_COOKIE_AGE_SECONDS
)
BASE_DIR = Path(__file__).resolve().parent.parent

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    "jazzmin",  # Giao diện admin hiện đại
    "django.contrib.admin",
    "django.contrib.staticfiles",
    "accounts.apps.AccountsConfig",
    "quizzes.apps.QuizzesConfig",
    "user_progress.apps.User_progressConfig",
    "courses.apps.CoursesConfig",
    "custom_admin.apps.Custom_adminConfig",
    "notifications.apps.NotificationsConfig",
    "django_recaptcha",
    'nested_admin',
    # Đưa các app xác thực và social auth xuống cuối
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "social_django",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "accounts.middleware.UserBlockMiddleware",
    "accounts.middleware.LoginRequiredMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware"
]

ROOT_URLCONF = "japanese_learning_platform.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'templates')],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "accounts.context_processors.user_context"
            ],
        },
    },
]
BASE_DIR = Path(__file__).resolve().parent.parent

TEMPLATES[0]["DIRS"] = [BASE_DIR / "templates"]

TEMPLATES[0]["OPTIONS"]["context_processors"] += [
    "core.context_processors.constants_context",
]

WSGI_APPLICATION = "japanese_learning_platform.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases


# Use SQLite for tests, PostgreSQL otherwise
import sys
if 'test' in sys.argv or 'pytest' in sys.argv[0]:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'test_db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation."
        "UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation."
        "MinimumLengthValidator",
        'OPTIONS': {
            'min_length': MIN_PASSWORD_LENGTH,
        }
    },
    {
        "NAME": "django.contrib.auth.password_validation."
        "CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation."
        "NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "vi"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/


STATIC_URL = "static/"
# STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",   # thư mục static ở cùng cấp manage.py
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Authentication
AUTH_USER_MODEL = 'accounts.User'  # Thay 'accounts' bằng tên app của bạn

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'social_core.backends.google.GoogleOAuth2',
    'accounts.utils.AuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]

LOGIN_EXEMPT_URLS = [
    '/accounts/login/',
    '/accounts/register/',
    '/accounts/forgot-password/',
    '/admin/',
    '/static/',
    '/media/',
]

# Login/Logout URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/accounts/profile/'
LOGOUT_REDIRECT_URL = '/'

#Admin_site
ADMIN_LOGIN_REDIRECT_URL = '/'

# Profile URLs
PROFILE_URL = '/accounts/profile/'
PROFILE_REDIRECT_URL = '/courses/courses_detail/'

# Email configuration (for verification)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = os.getenv('EMAIL_PORT')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'no-reply@test.dev'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

# Google OAuth settings
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv('GOOGLE_OAUTH2_CLIENT_ID')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv('GOOGLE_OAUTH2_CLIENT_SECRET')
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ['email', 'profile']
SOCIAL_AUTH_GOOGLE_OAUTH2_USE_UNIQUE_USER_ID = True
SOCIAL_AUTH_USER_MODEL = 'accounts.User'
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'accounts.pipeline.prevent_duplicate_social_email',
)
SOCIAL_AUTH_ASSOCIATE_BY_EMAIL = True
SOCIAL_AUTH_LOGIN_ERROR_URL = '/accounts/login/'

# Captcha
RECAPTCHA_PUBLIC_KEY = os.getenv('RECAPTCHA_PUBLIC_KEY')
RECAPTCHA_PRIVATE_KEY = os.getenv('RECAPTCHA_PRIVATE_KEY')

# Security settings
SESSION_COOKIE_AGE = SESSION_COOKIE_AGE_SECONDS
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
