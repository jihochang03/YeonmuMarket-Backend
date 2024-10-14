# user/urls.py
from django.urls import path
from .views import KakaoSignInCallbackView, SignOutView, TokenRefreshView,  KakaoLoginView, UserProfileListView, UserProfileDetailView, CheckUsernameView

app_name = "user"
urlpatterns = [
    path("signout/", SignOutView.as_view()),
    path("refresh/", TokenRefreshView.as_view()),
    path("userinfo/", UserProfileListView.as_view()),
    path("me/", UserProfileDetailView.as_view()),
    path("check/", CheckUsernameView.as_view()),
    path("kakao/login/", KakaoLoginView.as_view(), name="kakao-login"),  # 카카오 로그인 시작 URL
    path("kakao/callback/", KakaoSignInCallbackView.as_view()),  
]
