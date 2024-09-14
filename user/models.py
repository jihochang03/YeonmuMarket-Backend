from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    kakao_email = models.EmailField(default="")
    is_payment_verified = models.BooleanField(default=False)
    bank_account = models.OneToOneField('payments.BankAccount', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.kakao_email