from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import date

class Ticket(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    transferee = models.ForeignKey(User, related_name="ticket_transferee", null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=100, default='Untitled Ticket')
    description = models.CharField(max_length=255, blank=True, default='No description available')
    date = models.DateField(default=date.today)
    seat = models.CharField(max_length=50, default='General Admission')
    booking_details = models.CharField(max_length=100, default='No discounts applied')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    casting = models.CharField(max_length=100, default='Not specified')
    uploaded_file = models.FileField(upload_to='tickets/', null=True, blank=True)
    masked_file = models.FileField(upload_to='tickets/masked/', null=True, blank=True)  # 가려진 파일을 저장하는 필드
    
    STATUS_CHOICES = [
        ('transfer_pending', '양도 중'),
        ('transfer_completed', '양도 완료'),
        ('received_completed', '양수 완료'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='transfer_pending')
    
    def __str__(self):
        return self.title
