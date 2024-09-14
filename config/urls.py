from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.views.generic import TemplateView
from user.views import logout_view

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
    path('tickets/', include('tickets.urls')),  # tickets 앱의 URL 패턴 포함
    path('user/', include('user.urls')),  # user 관련 URL 통합
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('dashboard/', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),  # 대시보드 경로 추가
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('accounts/', include('allauth.urls')),  # allauth 경로 추가
    path('swagger/', schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path('payments/', include('payments.urls')),  # payments 앱 URL 연결
    path('conversations/', include('conversations.urls')),  # conversations 앱 URL 연결
    path('logout/', logout_view, name='logout'),  # 로그아웃 URL
]
