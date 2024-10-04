
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import TransferHistory
# from .kakao_api import send_message  

# @receiver(post_save, sender=TransferHistory)
# def notify_owner(sender, instance, created, **kwargs):
#     if created:
#         owner = instance.ticket.owner
#         message = f"New transfer request for your ticket: {instance.ticket.event_name}."
#         send_message(owner.kakao_id, message)  # KakaoTalk 메시지 전송 함수 호출

