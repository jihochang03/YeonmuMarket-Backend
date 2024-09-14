
# conversations/models.py
from django.db import models
from django.contrib.auth.models import User
from tickets.models import Ticket

class Conversation(models.Model):
    ticket = models.ForeignKey('tickets.Ticket', on_delete=models.CASCADE, null=True, blank=True)
    transferor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transferor_conversations',null=True, blank=True )
    transferee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transferee_conversations', null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Conversation for {self.ticket} between {self.transferor} and {self.transferee}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages',null=True, blank=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.username} at {self.sent_at}"
