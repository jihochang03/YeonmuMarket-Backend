import requests
from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from .models import UserProfile
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserProfileSerializer, UserSerializer

#카카오 로그인 링크 user/ login/kakao/로 접근하면 로그인 가능. 
def kakao_login(request):
    kakao_authorize_url = (
        "https://kauth.kakao.com/oauth/authorize"
        f"?client_id={settings.KAKAO_CLIENT_ID}"
        f"&redirect_uri={settings.KAKAO_REDIRECT_URI}"
        "&response_type=code"
    )
    return redirect(kakao_authorize_url)

#카카오 로그인으로 리디렉션. 
def login_view(request):
    return redirect(reverse('kakao_login'))

#로그아웃하면 로그인 페이지로 들어가지도록 user/ logout/
def logout_view(request):
    logout(request)
    return redirect('login')  # Redirect to login after logout

#카카오 로그인 후 콜백되어서 user에는 이메일이랑 랜덤 패스워드, userprofile에는 이메일이 들어가게 된다. 
#해당 계정이 인증된 계좌가 하나라도 있을 경우 홈화면으로 가게 되고 아닌 경우 검증하게 된다. 
def kakao_callback(request):
    code = request.GET.get('code')
    if not code:
        return redirect('login')

    access_token = get_kakao_access_token(code)
    if access_token:
        user_info = get_kakao_user_info(access_token)
        kakao_email = user_info.get('email')

        if kakao_email:
            user, created = User.objects.get_or_create(
                email=kakao_email,
                defaults={'username': kakao_email, 'password': User.objects.make_random_password()}
            )

            UserProfile.objects.update_or_create(
                user=user,
                defaults={'kakao_email': kakao_email}
            )

            login(request, user)

            user_profile = user.userprofile
            if not user_profile.is_payment_verified:
                return redirect('verify_bank_account')  
            
            return redirect('home')

    return redirect('login')

#로그인된 유저의 프로필을 보여줌
@login_required
def profile_view(request):
    profile = request.user.userprofile
    return render(request, 'profile.html', {'profile': profile})

def get_kakao_access_token(code):
    token_url = 'https://kauth.kakao.com/oauth/token'
    data = {
        'grant_type': 'authorization_code',
        'client_id': settings.KAKAO_CLIENT_ID,
        'redirect_uri': settings.KAKAO_REDIRECT_URI,
        'code': code,
    }
    response = requests.post(token_url, data=data)
    return response.json().get('access_token')

def get_kakao_user_info(access_token):
    user_info_url = 'https://kapi.kakao.com/v2/user/me'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(user_info_url, headers=headers)
    kakao_account = response.json().get('kakao_account', {})
    return {'email': kakao_account.get('email')}


#여기서부터는 그냥 장고 내에서 확인하려고 만든 뷰
class UserProfileDetail(generics.RetrieveUpdateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

    def get_object(self):
        user = self.request.user  # 현재 로그인된 사용자
        return get_object_or_404(UserProfile, user=user)

@csrf_exempt
@api_view(['POST'])
def create_user(request):
    if request.method == 'POST':
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileCreateView(generics.CreateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
