from pathlib import Path
import os
import environ
from datetime import timedelta
import dj_database_url
import pytesseract

pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

BASE_DIR = Path(__file__).resolve().parent.parent

# 환경 변수 로드
env = environ.Env(
    DEBUG=(bool, False)  # Default to False for production
)
environ.Env.read_env(env_file=os.path.join(BASE_DIR, '.env'))

# General settings
DEBUG = env.bool("DEBUG", default=False)
SECRET_KEY = env('SECRET_KEY')
KAKAO_KEY = env('KAKAO_KEY')
KAKAO_REDIRECT_URI = 'https://www.yeonmu.shop/auth'


# Allow only specified hosts
ALLOWED_HOSTS = ['api.yeonmu.shop', 'www.yeonmu.shop', 'yeonmu.shop']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'user',
    'tickets',
    'drf_yasg',
    'conversations',
    'payments',
    'django_extensions',
    'storages',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# CORS settings
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "https://www.yeonmu.shop",
    "https://api.yeonmu.shop",  # 배포된 React 주소를 추가할 경우
    "https://*.fly.dev",
]
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

CSRF_COOKIE_SAMESITE = None
SESSION_COOKIE_SAMESITE = None
CSRF_COOKIE_DOMAIN = ".yeonmu.shop"  # 최상위 도메인
CSRF_COOKIE_SAMESITE = "None"        # CORS 환경 허용
CSRF_TRUSTED_ORIGINS = [
    "https://api.yeonmu.shop",  # Fly.io 도메인
    "https://www.yeonmu.shop",  
    "https://*.fly.dev",
]
CORS_ALLOW_HEADERS = [
    "accept",
    "authorization",
    "content-type",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

DATABASES = {
    'default': dj_database_url.config(default=os.getenv('DATABASE_URL'))
}

# AWS S3 미디어 파일 설정
AWS_REGION = 'ap-northeast-2'  # S3 버킷의 리전 (서울)
AWS_STORAGE_BUCKET_NAME = 'yeonmubucket'


AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# S3에서 미디어 파일에 접근할 도메인 설정
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com'

# 미디어 파일 경로
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'  # S3 버킷의 미디어 경로
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# 미디어 파일 루트
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # 로컬 미디어 디렉토리 (개발용)


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        "user.authentication.CookieJWTAuthentication",
        'rest_framework.authentication.SessionAuthentication', 
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer', ),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken', ),
}

# Social account settings
SOCIALACCOUNT_LOGIN_ON_GET = True
LOGIN_URL = '/kakao/callback/'
LOGIN_REDIRECT_URL = '/'
ACCOUNT_SIGNUP_REDIRECT_URL = '/'
SOCIALACCOUNT_PROVIDERS = {
    'kakao': {
        'APP': {
            'client_id': env('KAKAO_KEY'),
            'secret': '',
            'key': ''
        }
    }
}

ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_VERIFICATION = 'none'
