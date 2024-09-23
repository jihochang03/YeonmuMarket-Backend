from rest_framework import serializers
from .models import Account, AccountVerification

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'account_number', 'bank_name', 'is_verified']

class AccountVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountVerification
        fields = ['id', 'account', 'verification_code']
