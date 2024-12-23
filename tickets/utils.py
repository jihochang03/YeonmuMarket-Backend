import hashlib
import uuid
from PIL import Image, ImageDraw
import pytesseract
from io import BytesIO
import cv2
import unicodedata
import re
import os

# Tesseract 설정
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"


def process_seat_image(image_file, booking_page):
    """좌석 이미지 처리 (좌석 정보 강조 표시)"""
    try:
        nparr = np.frombuffer(image_file.read(), np.uint8)
        cv_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if booking_page == "티켓링크":
            pil_image = draw_bounding_box_no_color_cv(cv_image)
        else:
            pil_image = draw_bounding_box_purple_cv(cv_image)

        # 처리된 이미지 반환
        buffer = BytesIO()
        pil_image.save(buffer, format="JPEG")
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(f"Error in seat image processing: {str(e)}")
        return None


def find_nearby_text(data, x, y, w, h, target_text):
    """주변 텍스트가 특정 문자열과 일치하는지 확인합니다."""
    for i in range(len(data['text'])):
        text_x, text_y, text_w, text_h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
        if abs(text_y - y) < 20 and (text_x > x + w and text_x < x + w + 50) and data['text'][i] == target_text:
            return True
    return False


def draw_bounding_box_no_color_cv(cv_image, width_scale=4):
    """좌석 이미지에 검정색 박스 그리기"""
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
    """좌석 이미지에 보라색 박스 그리기"""
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
