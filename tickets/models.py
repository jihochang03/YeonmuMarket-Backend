from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.files import File
import os
from .utils import normalize_filename, process_and_mask_image, process_seat_image
from PIL import Image, ImageDraw
import pytesseract
from django.conf import settings
import cv2
from io import BytesIO
import numpy as np
import unicodedata
import re
import uuid

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
    uploaded_file = models.FileField(upload_to="tickets/", null=True, blank=True)
    masked_file = models.FileField(upload_to="tickets/masked/", null=True, blank=True)
    uploaded_seat_image = models.FileField(upload_to="tickets/seats/", null=True, blank=True)
    processed_seat_image = models.FileField(upload_to="tickets/seats/processed/", null=True, blank=True)
    phone_last_digits = models.CharField(max_length=4, blank=True, null=True)

    STATUS_CHOICES = [
        ("waiting", "양수자 대기"),
        ("transfer_pending", "양도 중"),
        ("transfer_completed", "양도 완료"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="waiting")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.uploaded_file and not self.masked_file:
            self.process_and_save_masked_image()
        if self.uploaded_seat_image and not self.processed_seat_image:
            self.process_and_save_seat_image(self.booking_page)
        super().save(update_fields=["masked_file", "processed_seat_image"])

    def process_and_save_masked_image(self):
        if self.uploaded_file:
            try:
                masked_image = process_and_mask_image(self.uploaded_file)
                if masked_image:
                    file_name = f"ticket_{self.id}_masked.jpg"
                    self.masked_file.save(file_name, File(masked_image), save=True)
            except Exception as e:
                print(f"Error in masking process: {str(e)}")

    def process_and_save_seat_image(self, booking_page):
        if self.uploaded_seat_image:
            try:
                processed_image = process_seat_image(self.uploaded_seat_image, booking_page)
                if processed_image:
                    file_name = f"ticket_{self.id}_processed.jpg"
                    self.processed_seat_image.save(file_name, File(processed_image), save=True)
            except Exception as e:
                print(f"Error in seat image processing: {str(e)}")
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

