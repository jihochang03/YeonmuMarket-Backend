
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import TransferHistory
from .kakao_api import send_message  

@receiver(post_save, sender=TransferHistory)
def notify_owner(sender, instance, created, **kwargs):
    if created:
        

        owner = instance.ticket.owner
        message = f"New transfer request for your ticket: {instance.ticket.event_name}."
        send_message(owner.kakao_id, message)  # KakaoTalk 메시지 전송 함수 호출

import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Ticket
from django.conf import settings
import fitz  # PyMuPDF

# 예매번호 마스킹 함수
def mask_booking_number(input_pdf, output_pdf):
    pdf_document = fitz.open(input_pdf)

    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        page_width = page.rect.width
        text_instances = page.search_for("예매번호")

        for inst in text_instances:
            rect = fitz.Rect(0, inst.y0 - 10, page_width, inst.y1 + 10)
            page.draw_rect(rect, color=(0, 0, 0), fill=(0, 0, 0))

        page.update()

    pdf_document.save(output_pdf)

# 파일 업로드 후 처리
@receiver(post_save, sender=Ticket)
def process_ticket_file(sender, instance, created, **kwargs):
    if instance.uploaded_file and not instance.masked_file:  # 파일이 업로드되고 가려진 파일이 없는 경우
        original_file_path = instance.uploaded_file.path
        output_file_path = os.path.join(settings.MEDIA_ROOT, 'tickets/masked', f'masked_{os.path.basename(original_file_path)}')

        # 예매번호 마스킹 실행
        mask_booking_number(original_file_path, output_file_path)

        # masked_file 필드 업데이트
        instance.masked_file = f'tickets/masked/masked_{os.path.basename(original_file_path)}'
        instance.save()