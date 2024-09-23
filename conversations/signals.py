# conversation/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Conversation
from user.models import UserProfile

@receiver(post_save, sender=Conversation)
def update_user_points(sender, instance, **kwargs):
    """양도, 양수자의 포인트가 변경되면 자동으로 업데이트"""
    if not instance.transferee or not instance.owner:
        return

    if instance.transfer_complete():
        transferee_profile = UserProfile.objects.get(user=instance.transferee)
        transferor_profile = UserProfile.objects.get(user=instance.owner)
        
        ticket_price = instance.ticket.price

        # 포인트 변경 로직
        transferee_profile.remaining_points -= ticket_price
        transferor_profile.remaining_points += ticket_price

        # 저장
        transferee_profile.save()
        transferor_profile.save()

        print(f"{instance.transferee.username}의 포인트가 {ticket_price}만큼 감소했고, {instance.owner.username}의 포인트가 {ticket_price}만큼 증가했습니다.")
