from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import date

class Ticket(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, default='Untitled Ticket')  # 티켓 제목 with default
    description = models.CharField(max_length=255, blank=True, default='No description available')  # 티켓 설명 with default
    date = models.DateField(default=date.today)  # 티켓 날짜 with default to today's date
    seat = models.CharField(max_length=50, default='General Admission')  # 좌석 정보 with default
    booking_details = models.CharField(max_length=100, default='No discounts applied')  # 할인 정보 with default
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # 가격 with default
    casting = models.CharField(max_length=100, default='Not specified')  # 캐스팅 정보 with default
    uploaded_file = models.FileField(upload_to='tickets/', null=True, blank=True)  # 파일 업로드, no default needed

    def __str__(self):
        return self.title
class TransferHistory(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    transferee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transferee')
    transfer_date = models.DateTimeField(auto_now_add=True)
    conversation = models.OneToOneField('conversations.Conversation', on_delete=models.CASCADE,null=True, blank=True)

    def __str__(self):
        return f"Transfer on {self.transfer_date} for {self.ticket}"

class TransferRequest(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    buyer_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Transfer Request for {self.ticket} by {self.buyer}"

    def payment_verified(self):
        return True

    def mark_as_completed(self):
        self.completed = True
        self.save()
