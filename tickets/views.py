from django.shortcuts import render
from rest_framework.views import APIView
from drf_yasg import openapi
from rest_framework import status
from rest_framework.response import Response
from .models import Ticket, TicketPost
from .serializers import TicketSerializer, TicketPostSerializer
from drf_yasg.utils import swagger_auto_schema
import json
from django.db.models import Q
from .request_serializers import TicketPostListRequestSerializer, TicketPostDetailRequestSerializer
from user.models import User
from user.request_serializers import SignInRequestSerializer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from io import BytesIO
from PIL import Image, ImageDraw
from django.conf import settings
import pytesseract
from rest_framework.permissions import AllowAny
import re
import os
from django.http import JsonResponse
from rest_framework.decorators import api_view
import tweepy
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from conversations.models import Conversation  # Import Conversation model
from user.models import UserProfile
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, parser_classes, authentication_classes, permission_classes
import requests
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
import logging
import pytesseract
from datetime import datetime
import uuid
import base64
import hashlib
from unidecode import unidecode
from requests_oauthlib import OAuth1
import cv2
import numpy as np
from django.core.files import File
import pytesseract

pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

class TicketView(APIView):
    @swagger_auto_schema(
        operation_id="티켓 정보 조회",
        operation_description="티켓 정보를 조회합니다.",
        responses={201: TicketSerializer, 404: "Not Found", 400: "Bad Request"},
    )
    def get(self, request):
        try:
            ticket_id = request.data.get("ticket_id")
            ticket = Ticket.objects.get(id=ticket_id)
            serializer = TicketSerializer(instance=ticket)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Ticket.DoesNotExist:
            return Response({"detail": "Ticket not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
def sanitize_file_name(file_name):
    # 확장자 추출
    ext = file_name.split('.')[-1]
    base_name = file_name[:-(len(ext) + 1)]
    # unidecode로 한글, 특수문자 등을 ASCII 범위로 치환
    # 공백은 언더스코어(_)로 대체
    sanitized_name = unidecode(base_name).replace(" ", "_")
    return f"{sanitized_name}.{ext}"

def get_unique_file_path(file, prefix="uploads"):
    sanitized_name = sanitize_file_name(file.name)
    # 예: 93a2218ba6f14f48b09af5d7c3341db2_776a8246.jpg
    unique_name = f"{uuid.uuid4().hex}_{hashlib.md5(sanitized_name.encode()).hexdigest()[:8]}.{sanitized_name.split('.')[-1]}"

    
    # 최종 경로: uploads/2024/12/23/<unique_name>
    return f"{prefix}/{unique_name}"

# Logger 설정
logger = logging.getLogger("image_processing")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def process_and_mask_image(image):
    """
    이미지에서 민감한 정보를 마스킹하여 반환합니다.
    """
    try:
        logger.debug("Starting process_and_mask_image")
        draw = ImageDraw.Draw(image)

        # OCR로 텍스트 추출
        logger.debug("Running OCR on the image")
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, lang="kor")

        logger.debug(f"Extracted OCR data: {data}")
        
        for i in range(len(data['text'])):
                if '번' in data['text'][i]:
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    image_width = image.width
                    print(f"Found text '{data['text'][i]}' at position ({x}, {y}, {w}, {h})")  # 디버깅: 텍스트 위치 출력
                    if find_nearby_text(data, x, y, w, h, "매") or find_nearby_text(data, x, y, w, h, "호"):
                        print("Masking text area...")  # 디버깅: 텍스트 영역 마스킹
                        
                        draw.rectangle([(0, y - 10), (image_width, y + h + 10)], fill="black")
                    draw.rectangle([(0, y - 10), (image_width, y + h + 10)], fill="black")
    
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        buffer.seek(0)
        logger.debug("Masked image successfully created")
        return buffer

    except Exception as e:
        logger.exception("Error in masking process")
        return None


def process_seat_image(image_file, booking_page):
    """좌석 이미지 처리 (좌석 정보 강조 표시)"""
    try:
        logger.debug("Starting process_seat_image")
        # Pillow Image 객체를 BytesIO로 변환
        buffer = BytesIO()
        image_file.save(buffer, format="JPEG")
        buffer.seek(0)

        # BytesIO 객체에서 OpenCV 이미지로 변환
        nparr = np.frombuffer(buffer.read(), np.uint8)
        cv_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if booking_page == "티켓링크":
            logger.debug("Using no-color bounding box for 티켓링크")
            pil_image = draw_bounding_box_no_color_cv(cv_image)
        else:
            logger.debug("Using purple bounding box")
            pil_image = draw_bounding_box_purple_cv(cv_image)

        buffer = BytesIO()
        pil_image.save(buffer, format="JPEG")
        buffer.seek(0)
        logger.debug("Processed seat image successfully created")
        return buffer

    except Exception as e:
        logger.exception("Error in seat image processing")
        return None

def find_nearby_text(data, x, y, w, h, target_text):
    """Find nearby text matching the target."""
    for i in range(len(data['text'])):
        text_x, text_y, text_w, text_h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
        if abs(text_y - y) < 20 and (text_x > x + w and text_x < x + w + 50) and data['text'][i] == target_text:
            return True
    return False
    
def draw_bounding_box_no_color_cv(cv_image, width_scale=4):
    """좌석 이미지에 검정색 박스 그리기"""
    try:
        logger.debug("Starting draw_bounding_box_no_color_cv")
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
        logger.debug("Bounding box (no color) drawn successfully")
        return pil_image

    except Exception as e:
        logger.exception("Error in draw_bounding_box_no_color_cv")
        return None

def draw_bounding_box_purple_cv(cv_image, width_scale=4):
    """좌석 이미지에 보라색 박스 그리기"""
    try:
        logger.debug("Starting draw_bounding_box_purple_cv")
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
        logger.debug("Bounding box (purple) drawn successfully")
        return pil_image

    except Exception as e:
        logger.exception("Error in draw_bounding_box_purple_cv")
        return None


class TicketPostListView(APIView):
    def post(self, request):
        user = request.user
        if user.is_anonymous:
            return Response(
                {"detail": "인증되지 않은 사용자입니다. 로그인 후 시도해주세요."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if "reservImage" not in request.FILES or "seatImage" not in request.FILES:
            return Response(
                {"status": "error", "message": "Both reservImage and seatImage files are required."},
                status=400,
            )

        title = request.data.get("title")
        date = request.data.get("date")
        seat = request.data.get("seat")
        booking_details = request.data.get("booking_details")
        price = request.data.get("price")
        booking_page = request.data.get("booking_page")
        casting = request.data.get("casting")
        phone_last_digits = request.data.get("phone_last_digits")
        uploaded_file = request.FILES["reservImage"]
        uploaded_seat_image = request.FILES["seatImage"]

        try:
            # Ticket 객체 생성
            ticket = Ticket.objects.create(
                title=title,
                date=date,
                seat=seat,
                booking_details=booking_details,
                price=price,
                booking_page=booking_page,
                casting=casting,
                phone_last_digits=phone_last_digits,
                owner=user,
            )

            reserv_file_path = get_unique_file_path(uploaded_file, prefix=f"tickets/{ticket.id}")
            seat_file_path = get_unique_file_path(uploaded_seat_image, prefix=f"tickets/{ticket.id}")

            # 3) default_storage에 실제 저장
            reserv_path = default_storage.save(reserv_file_path, uploaded_file)
            seat_path = default_storage.save(seat_file_path, uploaded_seat_image)

            # 4) DB 필드에 URL 저장
            ticket.uploaded_file_url = default_storage.url(reserv_path)
            ticket.uploaded_seat_image_url = default_storage.url(seat_path)
        
            try:
                uploaded_file.seek(0)  # Ensure file pointer is at the beginning

                image = Image.open(BytesIO(uploaded_file.read()))
                logger.debug("Image loaded successfully for OCR")
                masked_image =process_and_mask_image(image)
                
                if masked_image:
                    masked_name = f"ticket_{ticket.id}_masked.jpg"
                    relative_path = f"tickets/{ticket.id}/{masked_name}"  # 상대 경로
                    masked_url = default_storage.save(relative_path, File(masked_image))
                    logger.debug(f"masked_url:{masked_url}")
                    ticket.masked_file_url = f"https://yeonmubucket.s3.ap-northeast-2.amazonaws.com/tickets/{ticket.id}/{masked_name}"
            except Exception as e:
                logger.exception("masked_File failed")
                return Response({"status": "error", "message": "masked_File failed"}, status=500)
            
            try:
                uploaded_seat_image.seek(0)  # Ensure file pointer is at the beginning

                image = Image.open(uploaded_seat_image)
                logger.debug("Image loaded successfully for OCR")
                masked_seat_image =process_seat_image(image,ticket.booking_page)
                
                if masked_seat_image:
                    masked_seat_name = f"ticket_{ticket.id}_processed.jpg"
                    relative_path = f"tickets/{ticket.id}/{masked_seat_name}"  # 상대 경로
                    masked_url = default_storage.save(relative_path, File(masked_seat_image))
                    logger.debug(f"masked_url:{masked_url}")
                    ticket.processed_seat_image_url =f"https://yeonmubucket.s3.ap-northeast-2.amazonaws.com/tickets/{ticket.id}/{masked_seat_name}"

            except Exception as e:
                logger.exception("masked_File failed")
                return Response({"status": "error", "message": "masked_File failed"}, status=500)
        
            ticket.save()

            # TicketPost 생성
            ticket_post = TicketPost.objects.create(ticket=ticket, author=user)

        except Exception as e:
            return Response({"detail": f"오류 발생: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = TicketPostSerializer(ticket_post, context={"request": request})
        response_data = serializer.data

        return Response(response_data, status=status.HTTP_201_CREATED)


class TicketPostDetailView(APIView):
    @swagger_auto_schema(
        operation_id="양도글 상세 조회",
        operation_description="양도글 1개의 상세 정보를 조회합니다.",
        responses={200: TicketPostSerializer, 400: "Bad Request"},
    )
    def get(self, request, ticket_post_id):
        try:
            ticket_post = TicketPost.objects.get(ticket__id=ticket_post_id)
        except TicketPost.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = TicketPostSerializer(ticket_post, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="티켓 양도글 삭제",
        operation_description="티켓 양도글을 삭제합니다.",
        request_body=None,
        responses={204: "No Content", 404: "Not Found", 400: "Bad Request"},
    )
    def delete(self, request, ticket_post_id):
        try:
            ticket_post = TicketPost.objects.get(ticket__id=ticket_post_id)
        except TicketPost.DoesNotExist:
            return Response({"detail": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        if request.user != ticket_post.author:
            return Response(
                {"detail": "You are not authorized to delete this post."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Delete associated ticket and conversation
            ticket = ticket_post.ticket
            Conversation.objects.filter(ticket=ticket).delete()

            # Delete files from storage
            if ticket.uploaded_file_url:
                default_storage.delete(ticket.uploaded_file_url)
            if ticket.masked_file_url:
                default_storage.delete(ticket.masked_file_url)
            if ticket.uploaded_seat_image_url:
                default_storage.delete(ticket.uploaded_seat_image_url)
            if ticket.processed_seat_image_url:
                default_storage.delete(ticket.processed_seat_image_url)

            # Delete Ticket and TicketPost
            ticket.delete()
            ticket_post.delete()

            return Response({"detail": "Ticket and TicketPost deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_id="티켓 양도글 수정",
        operation_description="티켓 양도글을 수정합니다.",
        request_body=TicketPostDetailRequestSerializer,
        responses={200: TicketPostSerializer, 404: "Not Found", 400: "Bad Request"},
    )
    def put(self, request, ticket_post_id):
        try:
            ticket_post = TicketPost.objects.get(ticket__id=ticket_post_id)
            ticket = ticket_post.ticket
        except TicketPost.DoesNotExist:
            return Response({"detail": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        if request.user != ticket_post.author:
            return Response(
                {"detail": "You are not authorized to edit this post."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Update fields dynamically
        update_fields = [
            "title",
            "date",
            "seat",
            "booking_details",
            "price",
            "booking_page",
            "casting",
            "phone_last_digits",
        ]
        for field in update_fields:
            value = request.data.get(field)
            if value is not None:
                setattr(ticket, field, value)

        # Handle file uploads (save to storage and update URL fields)
        if uploaded_file := request.FILES.get("uploaded_file"):
            reserv_path = default_storage.save(f"tickets/{ticket.id}/{uploaded_file.name}", uploaded_file)
            ticket.uploaded_file_url = default_storage.url(reserv_path)

        if uploaded_seat_image := request.FILES.get("uploaded_seat_image"):
            seat_path = default_storage.save(f"tickets/{ticket.id}/{uploaded_seat_image.name}", uploaded_seat_image)
            ticket.uploaded_seat_image_url = default_storage.url(seat_path)

        try:
            ticket.save()
            ticket_post.save()

            serializer = TicketPostSerializer(ticket_post, context={"request": request})
            response_data = serializer.data
            response_data["masked_seat_image_url"] = ticket.processed_seat_image_url

            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class TransferListView(APIView):
    @swagger_auto_schema(
        operation_id="양도 티켓 목록 조회",
        operation_description="사용자가 양도한 티켓 목록을 조회합니다.",
        responses={200: TicketSerializer(many=True), 404: "Not Found", 400: "Bad Request"},
    )
    def get(self, request):
        user = request.user
        transfer_list = Ticket.objects.filter(
            owner=user, status__in=['waiting', 'transfer_pending', 'transfer_completed']
        ).order_by('-id')

        if not transfer_list.exists():
            return Response({"detail": "No transferred tickets found."}, status=status.HTTP_404_NOT_FOUND)

        # context에 request를 전달
        serializer = TicketSerializer(transfer_list, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReceivedListView(APIView):
    @swagger_auto_schema(
        operation_id="양수 티켓 목록 조회",
        operation_description="사용자가 양수받은 티켓 목록을 조회합니다.",
        responses={200: TicketSerializer(many=True), 404: "Not Found", 400: "Bad Request"},
    )
    def get(self, request):
        user = request.user
        received_list = Ticket.objects.filter(
            transferee=user
        ).order_by('-id')

        if not received_list.exists():
            return Response({"detail": "No received tickets found."}, status=status.HTTP_404_NOT_FOUND)

        received_serializer = TicketSerializer(received_list, many=True, context={'request': request})
        return Response(received_serializer.data, status=status.HTTP_200_OK)
    
import logging

logger = logging.getLogger(__name__)
    
# Tesseract 경로 설정 (윈도우 경로 설정)
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

@swagger_auto_schema(
    method='post',
    operation_description="JPG 파일과 입력어(인터파크)를 받아 텍스트를 분석하고 예매 정보를 반환합니다.",
    manual_parameters=[
        openapi.Parameter('file', openapi.IN_FORM, description="이미지 파일 (JPG, PNG 형식)", type=openapi.TYPE_FILE),
        openapi.Parameter('keyword', openapi.IN_FORM, description="입력어 (인터파크, 예스24, 티켓링크)", type=openapi.TYPE_STRING),
    ],
    responses={200: '성공 시 예매 정보를 반환합니다.'}
)

# def process_image_for_ocr(image_data):
#     """
#     Process the image to improve OCR accuracy.
#     """
#     # 1. 이미지를 Pillow로 로드
#     image = Image.open(BytesIO(image_data))

#     # 2. 해상도 조정 (2배 확대)
#     base_width = 2000
#     w_percent = base_width / float(image.size[0])
#     h_size = int((float(image.size[1]) * float(w_percent)))
#     image = image.resize((base_width, h_size), Image.ANTIALIAS)

#     # 3. 흑백 변환 (이진화)
#     image = image.convert("L")
#     image = image.point(lambda x: 0 if x < 140 else 255)

#     # 4. 대비 조정
#     enhancer = ImageEnhance.Contrast(image)
#     image = enhancer.enhance(2.0)

#     # 5. 노이즈 제거 (OpenCV)
#     img_array = np.array(image)
#     denoised = cv2.fastNlMeansDenoising(img_array, None, h=30, templateWindowSize=7, searchWindowSize=21)
#     image = Image.fromarray(denoised)

#     return image

@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser])
def process_image(request):
    permission_classes = [AllowAny]
    try:
        # Step 1: Get and validate the keyword
        keyword = request.POST.get('keyword', '').strip()
        logger.debug(f"Received keyword: {keyword}")
        if not keyword:
            return Response({"status": "error", "message": "Keyword is required."}, status=400)

        # Step 2: Validate uploaded files
        if 'reservImage' not in request.FILES:
            logger.debug(f"Uploaded files: {request.FILES.keys()}")
            return Response({"status": "error", "message": "Both files are required."}, status=400)

        reserv_image = request.FILES['reservImage']

        try:
            reserv_image.seek(0)  # Ensure file pointer is at the beginning
            logger.debug("Starting OCR processing for reservImage")

            image = Image.open(BytesIO(reserv_image.read()))
            logger.debug("Image loaded successfully for OCR")

            extracted_text = pytesseract.image_to_string(image, lang="kor+eng")
            logger.debug(f"Raw extracted text: {extracted_text}")

        except Exception as e:
            logger.exception("OCR processing failed")
            return Response({"status": "error", "message": "OCR failed."}, status=500)

        #Step 5: Keyword-specific processing
        try:
            if keyword == '인터파크':
                response_data = process_interpark_data(extracted_text)
            elif keyword == '예스24':
                response_data = process_yes24_data(extracted_text)
            elif keyword == '티켓링크':
                response_data = process_link_data(extracted_text)
            else:
                logger.error(f"Invalid keyword provided: {keyword}")
                return Response({"status": "error", "message": "Invalid keyword."}, status=400)

            logger.debug(f"Processed data for keyword {keyword}: {response_data}")
        except Exception as e:
            logger.exception("Keyword processing failed")
            return Response({"status": "error", "message": f"Keyword processing failed: {str(e)}"}, status=500)

        # Step 6: Return response
        return Response(response_data, status=200)

    except Exception as e:
        logger.exception("Unexpected error during image processing")
        return Response({"status": "error", "message": f"Unexpected error: {str(e)}"}, status=500)


def process_link_data(extracted_text):
    try:
        reservation_status = check_reservation_status_link(extracted_text)
        date_info = extract_viewing_info_link(extracted_text)
        total_amount = extract_total_amount_link(extracted_text)
        price_grade = extract_discount_info_link(extracted_text)
        seat_number = extract_line_with_yeol_and_beon(extracted_text)
        place = extract_line_after_at_link(extracted_text)

        # 딕셔너리로 반환
        return {
            "status": "success",
            "reservation_status": reservation_status,
            "date_info": date_info,
            "total_amount": total_amount,
            "price_grade": price_grade,
            "seat_number": seat_number,
            "place": place,
        }
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    
def check_reservation_status_link(text):
    # '예매상태'와 그 옆의 텍스트 추출
    pattern = r'예매상태\s*(.*)'
    match = re.search(pattern, text)

    if not match:
        return ""

    reservation_status = match.group(1).strip()
    return reservation_status

def extract_viewing_info_link(text):
    # '관람일시'에서 날짜 및 시간 추출
    pattern = r'관람일시\s*(\d{4})\.(\d{2})\.(\d{2})\(\s*([\w가-힣]{1,3})\s*\)\s*(\d{2}):(\d{2})'
    match = re.search(pattern, text)

    if not match:
        return "관람 일시 정보를 찾을 수 없습니다."

    year, month, day, day_of_week, hour, minute = match.groups()

    # 딕셔너리 형태로 반환
    return {
        '관람년도': year,
        '관람월': month,
        '관람일': day,
        '요일': day_of_week,
        '시간': f"{hour}:{minute}"
    }

def extract_total_amount_link(text):
    # '총결제금액' 옆의 금액 추출
    pattern = r'총결제금액\s*(\d{1,3}(,\d{3})*)\s*원'
    match = re.search(pattern, text)

    if not match:
        return ""

    return match.group(1).replace(",", "")  # 숫자만 반환

def extract_line_after_at_link(text):
    # '장소' 이후의 모든 텍스트 추출
    pattern = r'장소\s*(.*)'
    match = re.search(pattern, text)

    if not match:
        return ""

    # '장소' 뒤의 내용을 공백 없이 추출
    location_info = match.group(1).strip()

    return location_info
    
def extract_line_with_yeol_and_beon(text):
    # '열'과 '번'이 포함된 줄 추출
    pattern = r'([가-힣]+열\s*\d+번)'
    match = re.search(pattern, text)

    if not match:
        return ""

    return match.group(1).strip() 

def extract_discount_info_link(text):
    # '할인' 관련 정보 추출
    pattern = r'결제정보\s*(\d{1,3}(,\d{3})*)\s*원'
    match = re.search(pattern, text)

    if not match:
        return ""

    discount_info = match.group(1).replace(",", "")
    return discount_info

def process_interpark_data(extracted_text):
    try:
        reservation_status = check_reservation_status_link(extracted_text)
        date_info = extract_viewing_info(extracted_text)
        ticket_number = extract_ticket_number(extracted_text)
        cast_info = extract_cast(extracted_text)
        total_amount = extract_total_amount(extracted_text)
        price_grade = extract_price_grade(extracted_text)
        seat_number = extract_seat_number(extracted_text)
        place = extract_line_after_at(extracted_text)

        return {
            "status": "success",
            "reservation_status": reservation_status,
            "date_info": date_info,
            "ticket_number": ticket_number,
            "cast_info": cast_info,
            "total_amount": total_amount,
            "price_grade": price_grade,
            "seat_number": seat_number,
            "place": place,
        }

    except ValueError as e:
        return JsonResponse({"status": "error", "message": str(e)})
# 아래는 예매 정보 추출을 위한 함수들 (기존 코드)


def extract_viewing_info(text):
    date_time_pattern = r'관 람 일 시\s*(\d{4})\.(\d{2})\.(\d{2})\(\s*(\w{1})\s*\)\s*(\d{2}):(\d{2})'
    match = re.search(date_time_pattern, text)

    if not match:
        return ""

    year, month, day, day_of_week, hour, minute = match.groups()
    result = {
        '관람년도': year,
        '관람월': month,
        '관람일': day,
        '관람시간': {
            '시': hour,
            '분': minute
        }
    }

    return result

def extract_ticket_number(text):
    ticket_number_pattern = r'예 매 번 호\s*([A-Za-z0-9]+)'
    match = re.search(ticket_number_pattern, text)

    if not match:
        return ""

    ticket_number = match.group(1)[-10:]
    result = f"T{ticket_number}"
    return result

def extract_cast(text):
    cast_pattern = r'주 요 출 연 진\s*(.*?)\s*티 켓 수 령 방 법'
    match = re.search(cast_pattern, text, re.DOTALL)

    if not match:
        return ""

    cast_lines = match.group(1).splitlines()
    cast_names = []
    for line in cast_lines:
        clean_line = line.strip()
        name_match = re.search(r'[\uAC00-\uD7A3]{1,2}\s*[\uAC00-\uD7A3]{1,2}\s*[\uAC00-\uD7A3]{1,2}$', clean_line)
        if name_match:
            full_name = name_match.group().replace(' ', '')
            last_three_chars = full_name[-3:]
            cast_names.append(last_three_chars)

    return cast_names

def extract_total_amount(text):
    amount_pattern = r'총 결 제 금 액.*?(\d{1,3}(,\d{3})*)\s*원'
    match = re.search(amount_pattern, text)

    if not match:
        return ""

    total_amount = match.group(1)
    return total_amount

def extract_price_grade(text):
    price_grade_pattern = r'가 격 등 급\s*_\s*(.*?)\s*%'
    match = re.search(price_grade_pattern, text)

    if not match:
        return ""

    price_grade = match.group(1).replace(' ', '')
    return price_grade

def extract_seat_number(text):
    seat_number_pattern = r'좌 석 번 호\s*_\s*(.*)'
    match = re.search(seat_number_pattern, text)

    if not match:
        return ""

    seat_number = match.group(1).replace(' ', '')
    return seat_number

def extract_line_after_at(text):
    at_pattern = r'@.*'
    match = re.search(at_pattern, text)

    if not match:
        return ""

    line_without_symbols = match.group(0)[1:].replace(' ', '').rstrip('>')
    return line_without_symbols

def process_yes24_data(extracted_text):
    try:
        # 예스24 관련 예매 상태 및 필요한 정보 추출 처리
        #reservation_status = check_reservation_status_yes24(extracted_text)
        date_info = extract_viewing_info_yes24(extracted_text)
        ticket_number = extract_ticket_number_yes24(extracted_text)
        total_amount = extract_total_amount_yes24(extracted_text)
        price_grade = extract_price_grade_yes24(extracted_text)
        seat_number = extract_seat_number_yes24(extracted_text)
        place = extract_line_after_at_yes24(extracted_text)

        return {
            "status": "success",
            #"reservation_status": reservation_status,
            "date_info": date_info,
            "ticket_number": ticket_number,
            "total_amount": total_amount,
            "price_grade": price_grade,
            "seat_number": seat_number,
            "place": place,
        }

    except ValueError as e:
        return JsonResponse({"status": "error", "message": str(e)})
# 예스24 관련 예매 상태 확인 함수 정의
def check_reservation_status_yes24(text):
    status_pattern = r'예 매 상 태\s*(.*)'
    match = re.search(status_pattern, text)
    
    if not match:
        raise ValueError("예매 상태 정보를 찾을 수 없습니다.")
    
    reservation_status = match.group(1).strip()
    
    return reservation_status

# 예스24 관련 날짜 정보 추출 함수
def extract_viewing_info_yes24(text):
    date_time_pattern = r'관 람 일 시\s*(\d{4})\.(\d{2})\.(\d{2})\s*(\d{2}):(\d{2})'
    match = re.search(date_time_pattern, text)

    if not match:
        return ""

    year, month, day, hour, minute = match.groups()

    result = {
        '관람년도': year,
        '관람월': month,
        '관람일': day,
        '관람시간': {
            '시': hour,
            '분': minute
        }
    }

    return result

# 예스24 관련 예매 번호 추출 함수
def extract_ticket_number_yes24(text):
    ticket_number_pattern = r'예 매 번 호\s*([A-Za-z0-9]+)'
    match = re.search(ticket_number_pattern, text)

    if not match:
        return ""

    ticket_number = match.group(1)[-10:]
    result = f"Y{ticket_number}"
    return result

# 예스24 관련 총 결제 금액 추출 함수
def extract_total_amount_yes24(text):
    amount_pattern = r'총 결 제 금 액.*?(\d{1,3}(,\d{3})*)\s*원'
    match = re.search(amount_pattern, text)

    if not match:
        return ""

    total_amount = match.group(1)
    return total_amount

# 예스24 관련 할인 금액 추출 함수
def extract_price_grade_yes24(text):
    line_pattern = r'할 인 금 액.*'
    line_match = re.search(line_pattern, text)

    if not line_match:
        return ""

    cleaned_line = line_match.group(0).replace(' ', '')
    
    reason_pattern = r'\(([^)]*)\)'
    reason_match = re.search(reason_pattern, cleaned_line)

    if not reason_match:
        return ""

    return reason_match.group(1)

# 예스24 관련 좌석 번호 추출 함수
def extract_seat_number_yes24(text):
    seat_pattern = r'좌 석 정 보\s*(.*)/'
    seat_match = re.search(seat_pattern, text)

    if not seat_match:
        return ""

    seat_info = seat_match.group(1).replace(' ', '')

    return seat_info

# 예스24 관련 극장명 추출 함수
def extract_line_after_at_yes24(text):
    pattern = r']\s*(.*?)\s*》'
    match = re.search(pattern, text)

    if not match:
        return ""

    extracted_text = match.group(1).replace(' ', '')

    return extracted_text


from TwitterAPI import TwitterAPI

# Twitter API Credentials
CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

@csrf_exempt
def post_tweet(request):
    permission_classes = [AllowAny]
    """
    Post a tweet with an optional image using TwitterAPI.
    """
    import json
    from io import BytesIO

    # 요청 데이터 읽기
    body = json.loads(request.body)
    tweet_content = body.get("tweetContent")  # 트윗 내용
    #image_path = body.get("imagePath")  # 이미지 경로 (Optional)

    if not tweet_content:
        return JsonResponse({"message": "트윗 내용이 비어 있습니다."}, status=400)

    # TwitterAPI 초기화
    api = TwitterAPI(
        CONSUMER_KEY,
        CONSUMER_SECRET,
        ACCESS_TOKEN,
        ACCESS_TOKEN_SECRET
    )

    try:
        # media_id = None
        # if image_path:  # 이미지가 제공된 경우
        #     with open(image_path, "rb") as f:
        #         data = f.read()
        #         response = api.request("media/upload", {"media_type": "image/jpeg"}, {"media": data})
        #         if response.status_code != 200:
        #             return JsonResponse(
        #                 {"message": "이미지 업로드 중 오류가 발생했습니다.", "error": response.json()},
        #                 status=response.status_code,
        #             )
        #         media_id = response.json().get("media_id_string")

        # 트윗 작성
        params = {"status": tweet_content}
        # if media_id:
        #     params["media_ids"] = media_id

        response = api.request("statuses/update", params)
        if response.status_code not in [200, 201]:
            return JsonResponse(
                {"message": "트윗 게시 중 오류가 발생했습니다.", "error": response.json()},
                status=response.status_code,
            )

        return JsonResponse(
            {"message": "트윗이 성공적으로 게시되었습니다.", "tweet": response.json()}
        )

    except Exception as e:
        return JsonResponse({"message": "알 수 없는 오류가 발생했습니다.", "error": str(e)}, status=500)
# def post_tweet(request):
#     # 로깅
#     logger.debug(f"Request content-type: {request.content_type}")
#     logger.debug(f"Request body: {request.body}")
#     """
#     Post a tweet using OAuth 1.0a Authentication
#     """
#     if request.content_type == "application/json":
#         body = json.loads(request.body)
#         tweet_content = body.get("tweetContent")
#     else:
#         # application/x-www-form-urlencoded
#         tweet_content = request.POST.get("tweetContent")
        
#     logger.debug(f"Extracted tweet_content: {tweet_content}")

#     # OAuth1 인증 객체 생성
#     auth = OAuth1(
#         CONSUMER_KEY,
#         CONSUMER_SECRET,
#         ACCESS_TOKEN,
#         ACCESS_TOKEN_SECRET
#     )

#     # Twitter API 요청
#     payload = {"status": tweet_content}
#     response = requests.post(TWITTER_API_URL, data=payload, auth=auth)
    
#     print("Twitter API Response Status:", response.status_code)
#     print("Twitter API Response Content:", response.json())


#     if response.status_code in [200, 201]:
#         return JsonResponse({"message": "트윗이 성공적으로 게시되었습니다.", "tweet": response.json()})
#     else:
#         return JsonResponse(
#             {"message": "트윗 게시 중 오류가 발생했습니다.", "error": response.json()},
#             status=response.status_code,
#         )