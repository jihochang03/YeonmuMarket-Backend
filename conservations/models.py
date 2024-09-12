from django.db import models
from django.contrib.auth.models import User
from tickets.models import Ticket

class Conversation(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    participants = models.ManyToManyField(User)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Conversation for Ticket {self.ticket.event_name}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Conversation for Ticket {self.ticket.seat}"