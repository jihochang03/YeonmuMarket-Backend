from django.db import models
from django.contrib.auth.models import User
from tickets.models import Ticket


class Exchange(models.Model):
    owner = models.ForeignKey(User, related_name='owner_exchange', on_delete=models.CASCADE)
    transferee = models.ForeignKey(User, related_name='transferee_exchange', on_delete=models.CASCADE, null=True, blank=True)
    ticket_1 = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='exchanges_as_ticket_1'  # 관련 이름 지정
    )
    ticket_2 = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='exchanges_as_ticket_2'  # 관련 이름 지정
    )
    transaction_step = models.IntegerField(default=0)  # Transaction progress tracking
    is_transfer_intent = models.BooleanField(default=False)
    is_acceptance_intent = models.BooleanField(default=False)

    def reset_transferee(self):
        self.transferee = None
        self.transaction_step = 0
        self.is_transfer_intent = False
        self.is_acceptance_intent = False
        self.save()
