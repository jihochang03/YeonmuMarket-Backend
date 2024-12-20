from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.files import File
import os
from PIL import Image, ImageDraw
import pytesseract
from django.conf import settings
import cv2
from io import BytesIO
import numpy as np
import unicodedata
import re

# Tesseract configuration
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"


class Ticket(models.Model):
    id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    transferee = models.ForeignKey(User, related_name="ticket_transferee", null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=255)
    date = models.DateField()
    seat = models.CharField(max_length=255)
    booking_page = models.CharField(max_length=255, default="인터파크")
    booking_details = models.CharField(max_length=100, default='No discounts applied')
    price = models.DecimalField(max_digits=10, decimal_places=0)
    casting = models.CharField(max_length=255)
    uploaded_file = models.FileField(upload_to='tickets/', null=True, blank=True)
    masked_file = models.FileField(upload_to='tickets/masked/', null=True, blank=True)
    uploaded_seat_image = models.FileField(upload_to='tickets/seats/', null=True, blank=True)
    processed_seat_image = models.FileField(upload_to='tickets/seats/processed/', null=True, blank=True)
    keyword = models.CharField(max_length=255, null=True, blank=True)
    phone_last_digits = models.CharField(max_length=4, blank=True, null=True)

    STATUS_CHOICES = [
        ('waiting', '양수자 대기'),
        ('transfer_pending', '양도 중'),
        ('transfer_completed', '양도 완료'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # 먼저 데이터베이스에 객체 저장
        if self.uploaded_file and not self.masked_file:
            self.process_and_save_masked_image()
        if self.uploaded_seat_image and not self.processed_seat_image:
            self.process_and_save_seat_image(self.keyword)
        super().save(update_fields=["masked_file", "processed_seat_image"])  # 업데이트된 필드만 저장


    @staticmethod
    def normalize_filename(filename):
        """Normalize filename to remove special characters and spaces, preserving the file extension."""
        filename, file_extension = os.path.splitext(filename)  # Split filename and extension
        filename = unicodedata.normalize("NFKD", filename)  # Normalize base filename
        filename = re.sub(r"[^\w\s-]", "", filename)  # Remove special characters
        filename = re.sub(r"[-\s]+", "-", filename).strip()  # Replace spaces with hyphens
    
        # Ensure the extension is '.jpg'
        if file_extension.lower() != '.jpg':
            file_extension = '.jpg'
    
        return f"{filename}{file_extension}"

    def process_and_save_masked_image(self):
        if self.uploaded_file:
            print("Opening uploaded file for masking...")  # 디버깅: 업로드된 파일 열기
            self.uploaded_file.open()
            image_data = self.uploaded_file.read()
            self.uploaded_file.close()

            image = Image.open(BytesIO(image_data))
            print("Extracting text using Tesseract...")  # 디버깅: Tesseract OCR 사용
            draw = ImageDraw.Draw(image)

            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, lang='kor')
            print("OCR Data:", data)  # 디버깅: OCR 결과 출력
            for i in range(len(data['text'])):
                if '번' in data['text'][i]:
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    print(f"Found text '{data['text'][i]}' at position ({x}, {y}, {w}, {h})")  # 디버깅: 텍스트 위치 출력
                    if find_nearby_text(data, x, y, w, h, "매") or find_nearby_text(data, x, y, w, h, "호"):
                        print("Masking text area...")  # 디버깅: 텍스트 영역 마스킹
                        image_width = image.width
                        draw.rectangle([(0, y - 10), (image_width, y + h + 10)], fill="black")

            output_image_name = self.normalize_filename(f"masked_{os.path.basename(self.uploaded_file.name)}")
            print(f"Saving masked image as {output_image_name}")  # 디버깅: 마스킹된 이미지 저장
            output_image = BytesIO()
            image.save(output_image, format='JPEG')
            output_image.seek(0)
            self.masked_file.save(output_image_name, File(output_image), save=True)

    def process_and_save_seat_image(self, keyword):
        if self.uploaded_seat_image:
            print("Opening uploaded seat image for processing...")  # 디버깅: 업로드된 좌석 이미지 열기
            self.uploaded_seat_image.open()
            image_data = self.uploaded_seat_image.read()
            self.uploaded_seat_image.close()

            nparr = np.frombuffer(image_data, np.uint8)
            cv_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if keyword == '티켓링크':
                print("Processing seat image with no color (black mask)...")  # 디버깅: 검은색 마스크 처리
                pil_image = draw_bounding_box_no_color_cv(cv_image)
            else:
                print("Processing seat image with purple mask...")  # 디버깅: 보라색 마스크 처리
                pil_image = draw_bounding_box_purple_cv(cv_image)

            output_image_name = self.normalize_filename(f"processed_{os.path.basename(self.uploaded_seat_image.name)}")
            print(f"Saving processed seat image as {output_image_name}")  # 디버깅: 처리된 좌석 이미지 저장
            output_image = BytesIO()
            pil_image.save(output_image, format='JPEG')
            output_image.seek(0)
            self.processed_seat_image.save(output_image_name, File(output_image), save=True)



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


# Utility Functions

def find_nearby_text(data, x, y, w, h, target_text):
    """Find nearby text matching the target."""
    for i in range(len(data['text'])):
        text_x, text_y, text_w, text_h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
        if abs(text_y - y) < 20 and (text_x > x + w and text_x < x + w + 50) and data['text'][i] == target_text:
            return True
    return False


def draw_bounding_box_no_color_cv(cv_image, width_scale=4):
    height, width, _ = cv_image.shape
    gray_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
    _, thresh_image = cv2.threshold(gray_image, 200, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    pil_image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_image)
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w > 5 and h > 5:
            box_x1 = max(0, x - w * (width_scale - 1) // 2)
            box_y1 = y
            box_x2 = min(width, x + w + w * (width_scale - 1) // 2)
            box_y2 = y + h
            draw.rectangle([box_x1, box_y1, box_x2, box_y2], outline="black", fill="black", width=3)
    return pil_image


def draw_bounding_box_purple_cv(cv_image, width_scale=4):
    height, width, _ = cv_image.shape
    hsv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
    lower_purple = (120, 50, 50)
    upper_purple = (140, 255, 255)
    mask = cv2.inRange(hsv_image, lower_purple, upper_purple)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    pil_image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_image)
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        box_x1 = max(0, x - w * (width_scale - 1) // 2)
        box_y1 = y
        box_x2 = min(width, x + w + w * (width_scale - 1) // 2)
        box_y2 = y + h
        draw.rectangle([box_x1, box_y1, box_x2, box_y2], outline="red", fill="red", width=3)
    return pil_image
