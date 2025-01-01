from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.files import File
import os
#from .utils import normalize_filename, process_and_mask_image, process_seat_image
from PIL import Image, ImageDraw
import pytesseract
from django.conf import settings
import cv2
from io import BytesIO
import numpy as np
import unicodedata
import re
from django.core.files.storage import default_storage
import uuid
from unidecode import unidecode
from datetime import datetime
import hashlib

class Ticket(models.Model):
    id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    transferee = models.ForeignKey(
        User, related_name="ticket_transferee", null=True, blank=True, on_delete=models.SET_NULL
    )
    title = models.CharField(max_length=255)
    date = models.DateField()
    seat = models.CharField(max_length=255)
    booking_page = models.CharField(max_length=255, default="인터파크")
    booking_details = models.CharField(max_length=100, default="No discounts applied")
    price = models.DecimalField(max_digits=10, decimal_places=0)
    casting = models.CharField(max_length=255)

    # 파일 저장 경로 대신 URL 저장
    uploaded_file_url = models.URLField(max_length=500, null=True, blank=True)
    masked_file_url = models.URLField(max_length=500, null=True, blank=True)
    uploaded_seat_image_url = models.URLField(max_length=500, null=True, blank=True)
    processed_seat_image_url = models.URLField(max_length=500, null=True, blank=True)

    phone_last_digits = models.CharField(max_length=4, blank=True, null=True)
    isTransfer = models.BooleanField(default=True)


    STATUS_CHOICES_TRANSFER = [
        ("waiting", "양수자 대기"),
        ("transfer_pending", "양도 중"),
        ("transfer_completed", "양도 완료"),
    ]
    STATUS_CHOICES_EXCHANGE = [
        ("waiting", "교환자 대기"),
        ("exchange_pending", "교환 중"),
        ("exchange_completed", "교환 완료"),
    ]
    status_transfer = models.CharField(max_length=20, choices=STATUS_CHOICES_TRANSFER, default="waiting")
    status_exchange = models.CharField(max_length=20, choices=STATUS_CHOICES_EXCHANGE, default="waiting")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class TicketPost(models.Model):
    ticket = models.OneToOneField(
        Ticket,
        primary_key=True,  # Use the ticket's ID as the primary key
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"TicketPost {self.ticket.id} by {self.author}"
