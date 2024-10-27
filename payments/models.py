from django.db import models
from django.contrib.auth.models import User

class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bank_account = models.CharField(max_length=16, default="0000000000000000")
    bank_name = models.CharField(max_length=100, default="")
    is_payment_verified = models.BooleanField(default=False)


