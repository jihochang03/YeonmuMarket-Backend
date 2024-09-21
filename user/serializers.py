from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from .models import UserProfile
from payments.models import BankAccount
from django.contrib.auth.models import User

class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = ['account_number', 'bank_name']

class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "password"]

class UserProfileSerializer(ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = UserProfile
        fields = "__all__"