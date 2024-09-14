from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from allauth.socialaccount.signals import social_account_added
from .models import UserProfile

# 사용자 인스턴스가 생성될 때마다 호출되는 신호 처리기
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    새로운 사용자가 생성되면 자동으로 UserProfile을 생성.
    - sender: 신호를 보내는 모델(여기서는 User)
    - instance: 신호를 보낸 User 인스턴스
    - created: 인스턴스가 새로 생성되었는지 여부 (True면 새로 생성된 것)
    """
    if created:
        # 새로 생성된 사용자에 대해 UserProfile을 생성합니다.
        UserProfile.objects.create(user=instance)

# 사용자 인스턴스가 저장될 때마다 호출되는 신호 처리기
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    사용자가 저장될 때마다 해당 사용자와 연결된 UserProfile을 저장.
    만약 UserProfile이 존재하지 않으면 새로 생성.
    - sender: 신호를 보내는 모델(여기서는 User)
    - instance: 신호를 보낸 User 인스턴스
    """
    try:
        # 사용자의 UserProfile을 저장.
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        # UserProfile이 존재하지 않는 경우 새로 생성.
        UserProfile.objects.create(user=instance)

# 소셜 로그인 계정이 추가될 때 호출되는 신호 처리기
@receiver(social_account_added)
def social_login_callback(request, sociallogin, **kwargs):
    """
    소셜 로그인 계정이 추가되었을 때 호출.
    소셜 로그인 정보에서 카카오 이메일을 가져와 UserProfile에 저장.
    - request: HTTP 요청 객체
    - sociallogin: 추가된 소셜 로그인 계정에 대한 정보
    """
    user = sociallogin.user
    # UserProfile을 가져오거나 새로 생성.
    profile, created = UserProfile.objects.get_or_create(user=user)
    if created or not profile.kakao_email:
        # 카카오 로그인 계정에서 카카오 이메일을 가져옴.
        kakao_account = sociallogin.account.extra_data.get('kakao_account', {})
        profile.kakao_email = kakao_account.get('email', '')
        profile.save()