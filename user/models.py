from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profilepic_id = models.IntegerField(null=True, blank=True)
    nickname = models.CharField(max_length=256, blank=True, null=True)
    remaining_points = models.IntegerField(default=0)
    is_social_login = models.BooleanField(default=False)
    kakao_email = models.EmailField(default="")
    is_payment_verified = models.BooleanField(default=False)
    bank_account = models.OneToOneField('payments.BankAccount', null=True, blank=True, on_delete=models.SET_NULL)
    kakao_token = models.CharField(max_length=256, blank=True, null=True)  # 카카오톡 액세스 토큰 추가
