from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from .models import UserProfile
from django.contrib.auth.models import User

class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "password"]

class UserProfileSerializer(ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = UserProfile
        fields = "__all__"