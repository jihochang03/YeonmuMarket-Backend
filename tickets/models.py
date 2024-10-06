from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import date
from django.core.files import File
import os
from PIL import Image, ImageDraw
import pytesseract
from django.conf import settings
import cv2

# Tesseract 경로 설정
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class Ticket(models.Model):
    id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    transferee = models.ForeignKey(User, related_name="ticket_transferee", null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=100, default='Untitled Ticket')
    date = models.DateField(default=date.today)
    seat = models.CharField(max_length=50, default='General Admission')
    booking_details = models.CharField(max_length=100, default='No discounts applied')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    casting = models.CharField(max_length=100, default='Not specified')
    uploaded_file = models.FileField(upload_to='tickets/', null=True, blank=True)
    masked_file = models.FileField(upload_to='tickets/masked/', null=True, blank=True)  # 가려진 파일을 저장하는 필드
    uploaded_seat_image = models.FileField(upload_to='tickets/seats/', null=True, blank=True)  # 좌석 사진 저장
    processed_seat_image = models.FileField(upload_to='tickets/seats/processed/', null=True, blank=True) # 처리된 좌석 사진 저장
    phone_last_digits = models.CharField(max_length=4, blank=True, null=True) 
    
    STATUS_CHOICES = [
        ('transfer_pending', '양도 중'),
        ('transfer_completed', '양도 완료'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='transfer_pending')
    
    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        keyword = kwargs.pop('keyword', None)  # save 메서드 호출 시 keyword를 전달받음
        super().save(*args, **kwargs)
        
        # 예매 내역 파일 마스킹 처리
        if self.uploaded_file and not self.masked_file:
            self.process_and_save_masked_image()
        
        # 좌석 이미지 처리
        if self.uploaded_seat_image and not self.processed_seat_image:
            self.process_and_save_seat_image(keyword)

    def process_and_save_masked_image(self):
        if self.uploaded_file:
            input_image_path = self.uploaded_file.path
            output_image_name = f"masked_{os.path.basename(self.uploaded_file.name)}"
            output_image_path = os.path.join(settings.MEDIA_ROOT, 'tickets/masked', output_image_name)

            # 폴더가 없으면 생성
            os.makedirs(os.path.dirname(output_image_path), exist_ok=True)

            # 이미지 마스킹 처리
            if mask_booking_number_in_image(input_image_path, output_image_path):
                with open(output_image_path, 'rb') as f:
                    self.masked_file.save(output_image_name, File(f), save=True)

    def process_and_save_seat_image(self, keyword):
        if self.uploaded_seat_image:
            input_image_path = self.uploaded_seat_image.path
            output_image_name = f"processed_{os.path.basename(self.uploaded_seat_image.name)}"
            output_image_path = os.path.join(settings.MEDIA_ROOT, 'tickets/seats/processed', output_image_name)

            # 폴더가 없으면 생성
            os.makedirs(os.path.dirname(output_image_path), exist_ok=True)

            # 좌석 이미지 처리 (keyword에 따라 분기 처리)
            if keyword == '티켓링크':
                draw_bounding_box_no_color(input_image_path, output_image_path)
            else:
                draw_bounding_box_purple(input_image_path, output_image_path)

            # 처리된 파일 저장
            with open(output_image_path, 'rb') as f:
                self.processed_seat_image.save(output_image_name, File(f), save=True)

# 이미지 처리 함수는 따로 정의하여 사용
def find_nearby_text(data, x, y, w, h, target_text):
    for i in range(len(data['text'])):
        text_x, text_y, text_w, text_h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
        text = data['text'][i]
        if abs(text_y - y) < 20 and (text_x > x + w and text_x < x + w + 50) and text == target_text:
            return True
    return False

def mask_booking_number_in_image(input_image_path, output_image_path):
    try:
        image = Image.open(input_image_path)
        draw = ImageDraw.Draw(image)

        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, lang='kor')
        n_boxes = len(data['text'])
        found = False
        for i in range(n_boxes):
            if '번' in data['text'][i]:
                (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
                if find_nearby_text(data, x, y, w, h, "매") or find_nearby_text(data, x, y, w, h, "호"):
                    found = True
                    image_width = image.width
                    draw.rectangle([(0, y - 10), (image_width, y + h + 10)], fill="black")

        if found:
            image.save(output_image_path)
            return True
        else:
            return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

# 보라색 좌석 감지
def draw_bounding_box_purple(image_path, output_path, width_scale=4):
    if not os.path.exists(image_path):
        return
    
    image = cv2.imread(image_path)
    if image is None:
        return
    
    height, width, _ = image.shape
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_purple = (120, 50, 50)
    upper_purple = (140, 255, 255)
    mask = cv2.inRange(hsv_image, lower_purple, upper_purple)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    pil_image = Image.open(image_path)
    draw = ImageDraw.Draw(pil_image)
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        box_x1 = max(0, x - w * (width_scale - 1) // 2)
        box_y1 = y
        box_x2 = min(width, x + w + w * (width_scale - 1) // 2)
        box_y2 = y + h
        draw.rectangle([box_x1, box_y1, box_x2, box_y2], outline="red", fill="red", width=3)

    pil_image.save(output_path)

# 색상 무관한 좌석 감지
def draw_bounding_box_no_color(image_path, output_path, width_scale=4):
    if not os.path.exists(image_path):
        return
    
    image = cv2.imread(image_path)
    if image is None:
        return
    
    height, width, _ = image.shape
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh_image = cv2.threshold(gray_image, 200, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    pil_image = Image.open(image_path)
    draw = ImageDraw.Draw(pil_image)
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w > 5 and h > 5:
            box_x1 = max(0, x - w * (width_scale - 1) // 2)
            box_y1 = y
            box_x2 = min(width, x + w + w * (width_scale - 1) // 2)
            box_y2 = y + h
            draw.rectangle([box_x1, box_y1, box_x2, box_y2], outline="black", fill="black", width=3)

    pil_image.save(output_path)


class TicketPost(models.Model):
    id = models.AutoField(primary_key=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE) # or one to one 
 
    created_at = models.DateTimeField(auto_now_add=True)