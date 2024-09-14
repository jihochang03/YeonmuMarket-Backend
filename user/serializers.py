from rest_framework import serializers
from .models import UserProfile
from payments.models import BankAccount
from django.contrib.auth.models import User

class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = ['account_number', 'bank_name']

class UserProfileSerializer(serializers.ModelSerializer):
    bank_account = BankAccountSerializer(read_only=True)  # Include bank account details

    class Meta:
        model = UserProfile
        fields = ['user', 'kakao_email', 'is_payment_verified', 'bank_account']
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user