# models.py
from django.db import models
from django.contrib.auth.models import User
from tickets.models import Ticket

class Conversation(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, related_name='owner_conversations', on_delete=models.CASCADE)
    transferee = models.ForeignKey(User, related_name='transferee_conversations', on_delete=models.CASCADE, null=True, blank=True)
    transaction_step = models.IntegerField(default=0)  # Transaction progress tracking
    is_transfer_intent = models.BooleanField(default=False)
    is_acceptance_intent = models.BooleanField(default=False)

    def reset_transferee(self):
        self.transferee = None
        self.transaction_step = 0
        self.is_transfer_intent = False
        self.is_acceptance_intent = False
        self.save()
