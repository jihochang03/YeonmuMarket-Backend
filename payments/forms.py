from django import forms
from .models import BankAccount

class BankAccountForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = ['account_number', 'bank_name']

class VerifyBankAccountForm(forms.Form):
    verification_code = forms.CharField(max_length=4)  # For entering the sender's name

class PaymentForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2)
