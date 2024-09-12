import requests
from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import UserProfile

def kakao_login(request):
    kakao_authorize_url = (
        "https://kauth.kakao.com/oauth/authorize"
        f"?client_id={settings.KAKAO_CLIENT_ID}"
        f"&redirect_uri={settings.KAKAO_REDIRECT_URI}"
        "&response_type=code"
    )
    return redirect(kakao_authorize_url)

def logout_view(request):
    logout(request)
    return redirect('login')  # Redirect to login after logout

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
            return redirect('list_ticket')

    return redirect('login')

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

def login_view(request):
    return redirect(reverse('kakao_login'))
