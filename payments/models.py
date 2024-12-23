from django.db import models
from django.contrib.auth.models import User

class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    bank_account = models.CharField(max_length=16, default="0000000000000000")
    bank_name = models.CharField(max_length=100, default="")
    account_holder = models.CharField(max_length=100, default="")  # 계좌 소유자 이름 추가
    is_payment_verified = models.BooleanField(default=False)


