from django.db import models
from django.contrib.auth.models import User
from user.models import UserProfile
from tickets.models import Ticket
from django.db.models.signals import post_save
from django.dispatch import receiver

class Conversation(models.Model):
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, related_name="conversation_owner", on_delete=models.CASCADE)
    transferee = models.ForeignKey(User, related_name="conversation_transferee", null=True, blank=True, on_delete=models.SET_NULL)
    is_transfer_intent = models.BooleanField(default=False)
    is_acceptance_intent = models.BooleanField(default=False)

    def can_join(self, user):
        """Only allow new transferee if there's no transferee and the user is not the owner"""
        return self.transferee is None and user != self.owner

    def reset_transferee(self):
        """Reset the transferee and transfer intent"""
        self.transferee = None
        self.is_acceptance_intent = False
        self.save()

    def transfer_complete(self):
        """Check if both parties have indicated transfer intent"""
        return self.is_transfer_intent and self.is_acceptance_intent

    def check_sufficient_points(self):
        """Check if the transferee has enough points to complete the transaction"""
        transferee_profile = UserProfile.objects.get(user=self.transferee)
        ticket_price = self.ticket.price
        return transferee_profile.remaining_points >= ticket_price


@receiver(post_save, sender=Conversation)
def update_user_points(sender, instance, **kwargs):
    """Automatically update points for both transferor and transferee when transfer is complete"""
    if not instance.transferee or not instance.owner:
        return

    if instance.transfer_complete():
        transferee_profile = UserProfile.objects.get(user=instance.transferee)
        transferor_profile = UserProfile.objects.get(user=instance.owner)
        
        ticket_price = instance.ticket.price

        # Check if transferee has enough points
        if transferee_profile.remaining_points < ticket_price:
            print(f"{instance.transferee.username} does not have enough points.")
            return  # 거래 중단

        # Update points
        transferee_profile.remaining_points -= ticket_price
        transferor_profile.remaining_points += ticket_price

        # Save updated profiles
        transferee_profile.save()
        transferor_profile.save()

        print(f"{instance.transferee.username}의 포인트가 {ticket_price}만큼 감소했고, {instance.owner.username}의 포인트가 {ticket_price}만큼 증가했습니다.")
