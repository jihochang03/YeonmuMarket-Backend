from django.urls import path
from .views import kakao_login, logout_view, kakao_callback, profile_view, login_view

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('login/kakao/', kakao_login, name='kakao_login'),
    path('login/kakao/callback/', kakao_callback, name='kakao_callback'),
    path('profile/', profile_view, name='profile'),
]
