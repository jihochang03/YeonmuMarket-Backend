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
            self.process_and_save_seat_image(self.keyword)
        super().save(update_fields=["masked_file", "processed_seat_image"])

    @staticmethod
    def normalize_filename(filename):
        """Normalize filename to remove special characters and spaces, preserving the file extension."""
        filename, file_extension = os.path.splitext(filename)
        filename = unicodedata.normalize("NFKD", filename)
        filename = re.sub(r"[^\w\s-]", "", filename)
        filename = re.sub(r"[-\s]+", "-", filename).strip()

        if file_extension.lower() not in [".jpg", ".jpeg", ".png"]:
            file_extension = ".jpg"

        return f"{filename}{file_extension}"

    @staticmethod
    def get_unique_file_path(file_name, prefix="uploads"):
        """Generate a unique file path with a date-based folder structure."""
        sanitized_name = Ticket.normalize_filename(file_name)
        unique_name = f"{uuid.uuid4().hex}_{hashlib.md5(sanitized_name.encode()).hexdigest()[:8]}.{sanitized_name.split('.')[-1]}"
        today = datetime.now().strftime("%Y/%m/%d")
        return f"{prefix}/{today}/{unique_name}"

    def process_and_save_masked_image(self):
        if self.uploaded_file:
            try:
                self.uploaded_file.open()
                image_data = self.uploaded_file.read()
                self.uploaded_file.close()

                image = Image.open(BytesIO(image_data))
                draw = ImageDraw.Draw(image)

                data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, lang="kor")
                for i in range(len(data["text"])):
                    if "번" in data["text"][i]:
                        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                        if find_nearby_text(data, x, y, w, h, "매") or find_nearby_text(data, x, y, w, h, "호"):
                            image_width = image.width
                            draw.rectangle([(0, y - 10), (image_width, y + h + 10)], fill="black")

                output_image_name = self.get_unique_file_path(f"masked_{os.path.basename(self.uploaded_file.name)}")
                output_image = BytesIO()
                image.save(output_image, format="JPEG")
                output_image.seek(0)
                self.masked_file.save(output_image_name, File(output_image), save=True)
            except Exception as e:
                print(f"Error in masking process: {str(e)}")

    def process_and_save_seat_image(self, keyword):
        if self.uploaded_seat_image:
            try:
                self.uploaded_seat_image.open()
                image_data = self.uploaded_seat_image.read()
                self.uploaded_seat_image.close()

                nparr = np.frombuffer(image_data, np.uint8)
                cv_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if keyword == "티켓링크":
                    pil_image = draw_bounding_box_no_color_cv(cv_image)
                else:
                    pil_image = draw_bounding_box_purple_cv(cv_image)

                output_image_name = self.get_unique_file_path(f"processed_{os.path.basename(self.uploaded_seat_image.name)}")
                output_image = BytesIO()
                pil_image.save(output_image, format="JPEG")
                output_image.seek(0)
                self.processed_seat_image.save(output_image_name, File(output_image), save=True)
            except Exception as e:
                print(f"Error in seat image processing: {str(e)}")
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

