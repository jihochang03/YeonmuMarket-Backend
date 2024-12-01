from rest_framework import serializers
from .models import Account

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['bank_account', 'bank_name', 'account_holder', 'is_payment_verified']

    def save(self, user=None):
        """
        Save the Account instance with the validated data.
        """
        # Check if the user is provided
        if not user:
            raise serializers.ValidationError({"detail": "User must be provided."})

        # Create or update the Account instance
        account, created = Account.objects.update_or_create(
            user=user,
            defaults={
                "bank_account": self.validated_data['bank_account'],
                "bank_name": self.validated_data['bank_name'],
                "account_holder": self.validated_data['account_holder'],
                'is_payment_verified':self.validated_data['is_payment_verified'],
            },
        )

        return account

