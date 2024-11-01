from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profilepic_id = models.IntegerField(null=True, blank=True)
    nickname = models.CharField(max_length=256, blank=True, null=True)
    is_social_login = models.BooleanField(default=False)
    kakao_email = models.EmailField(default="")
    # is_payment_verified = models.BooleanField(default=True)
    # bank_account = models.CharField(max_length=20, null=True, blank=True)
    # bank_name = models.CharField(max_length=100, null=True, blank=True)
    kakao_token = models.CharField(max_length=256, blank=True, null=True)  # 카카오톡 액세스 토큰 추가

    def __str__(self):
        return self.nickname or self.user.username