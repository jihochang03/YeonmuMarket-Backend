from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi 
from django.conf.urls.static import static
from django.conf import settings
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
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/tickets/', include('tickets.urls')),  # tickets 앱의 URL 패턴 포함
    path('api/user/', include('user.urls')),  # user 관련 URL 통합
    path('swagger/', schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/payments/', include('payments.urls')),  # payments 앱 URL 연결
    path('api/point/', include('Point.urls')),
    path('api/conversations/', include('conversations.urls')),  # conversations 앱 URL 연결
]
# 개발 중 미디어 파일 서빙 설정
if settings.DEBUG:  # 개발 환경에서만 미디어 파일 서빙
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)