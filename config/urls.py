from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi 
from rest_framework.permissions import AllowAny
from django.conf.urls.static import static
from django.conf import settings
import os
from pathlib import Path
import environ
from user.views import KakaoLoginView, KakaoSignInCallbackView

BASE_DIR = Path(__file__).resolve().parent.parent

# 환경 변수 로드
env = environ.Env(
    DEBUG=(bool, False)  # Default to False for production
)
environ.Env.read_env(env_file=os.path.join(BASE_DIR, '.env'))
# Swagger 관련 설정
schema_view = get_schema_view(
    openapi.Info(
        title="API Docs",
        default_version='v1',
        description="API documentation",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@myapi.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(AllowAny,),  # 누구나 접근 가능
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/tickets/', include('tickets.urls')),  # tickets 앱의 URL 패턴 포함
    path('api/user/', include('user.urls')),  # user 관련 URL 통합
    path('swagger/', schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/payments/', include('payments.urls')),  # payments 앱 URL 연결
    path('api/conversations/', include('conversations.urls')),  # conversations 앱 URL 연결
    # path('api/kakao/login/', KakaoLoginView.as_view(), name='kakao-login'),
    # path('api/kakao/callback/', KakaoSignInCallbackView.as_view(), name='kakao-callback'),
]

# AWS S3 미디어 파일 설정
AWS_REGION = 'ap-northeast-2'  # S3 버킷의 리전 (서울)
AWS_STORAGE_BUCKET_NAME = 'yeonmubucket'  # S3 버킷 이름
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')  # 환경 변수에서 가져오기
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')  # 환경 변수에서 가져오기

# S3에서 미디어 파일에 접근할 도메인 설정
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com'

# 개발 중 미디어 파일 서빙 설정
if settings.DEBUG:  # 개발 환경에서만 미디어 파일 서빙
    # 로컬 개발 환경에서는 로컬에 미디어 파일 저장
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
else:
    # 프로덕션 환경에서는 S3에 미디어 파일 저장
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
    