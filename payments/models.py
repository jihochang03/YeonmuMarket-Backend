from django.db import models
from django.contrib.auth.models import User

class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=50, unique=True)
    bank_name = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)  # 기본값 설정
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class AccountVerification(models.Model):
    account = models.OneToOneField(Account, on_delete=models.CASCADE)
    verification_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
