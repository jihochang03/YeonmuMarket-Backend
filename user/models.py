from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    kakao_email = models.EmailField(default="")

    def __str__(self):
        return self.kakao_email
