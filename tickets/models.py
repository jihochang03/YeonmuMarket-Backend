from django.db import models
from django.contrib.auth.models import User

class Ticket(models.Model):
    date = models.DateField(auto_now_add=True)
    seat = models.CharField(max_length=100, default="")
    booking_details = models.TextField(default="Default booking details")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    casting = models.CharField(max_length=100, default="")
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.date} - {self.seat}"

class TransferHistory(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    transferee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transferee')
    transfer_date = models.DateTimeField(auto_now_add=True)
    conversation = models.OneToOneField('conversations.Conversation', on_delete=models.CASCADE,null=True, blank=True)

    def __str__(self):
        return f"Transfer on {self.transfer_date} for {self.ticket}"

class TransferRequest(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    buyer_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Transfer Request for {self.ticket} by {self.buyer}"

    def payment_verified(self):
        return True

    def mark_as_completed(self):
        self.completed = True
        self.save()
