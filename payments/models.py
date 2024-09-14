from django.db import models
from django.contrib.auth.models import User

class BankAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=100)
    bank_name = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.account_number} - {self.bank_name}"
class Payment(models.Model):
    transfer_request = models.OneToOneField('tickets.TransferRequest', on_delete=models.CASCADE)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Payment for {self.transfer_request} - {'Paid' if self.is_paid else 'Pending'}"
