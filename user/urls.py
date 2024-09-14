from django.urls import path
from .views import kakao_login, logout_view, kakao_callback, profile_view, login_view, UserProfileCreateView, create_user, UserProfileDetail

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('login/kakao/', kakao_login, name='kakao_login'),
    path('login/kakao/callback/', kakao_callback, name='kakao_callback'),
    path('profile/', profile_view, name='profile'),
    #여기서부터는 그냥 장고 내에서 확인하려고 만든 url
    path('create/', UserProfileCreateView.as_view(), name='user_profile_create'),
    path('create_user/', create_user, name='create_user'),
    path('user_profiles/<int:pk>/', UserProfileDetail.as_view(), name='user_profile_detail'),
]