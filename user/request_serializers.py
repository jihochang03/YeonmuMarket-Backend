from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from django.contrib.auth.models import User

class SignUpRequestSerializer(serializers.Serializer):
    password = serializers.CharField()
    username = serializers.CharField()
class SignInRequestSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "password"]

class TokenRefreshRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class SignOutRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class UserProfileUpdateRequestSerializer(serializers.Serializer):
    profilepic_id = serializers.IntegerField()
    nickname = serializers.CharField()