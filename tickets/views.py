from django.shortcuts import render
from rest_framework.views import APIView
from drf_yasg import openapi
from rest_framework import status
from rest_framework.response import Response
from .models import Ticket, TicketPost
from .serializers import TicketSerializer, TicketPostSerializer
from exchange.serializers import ExchangeSerializer
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
from exchange.models import Exchange
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
import boto3
from botocore.exceptions import ClientError
from django.http import HttpResponse, Http404
from django.conf import settings


pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# S3 설정
AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY
AWS_STORAGE_BUCKET_NAME = "yeonmubucket"
AWS_REGION = "ap-northeast-2"  # S3 버킷의 리전

@api_view(["GET"])
def download_image(request, file_key):
    """
    S3에서 파일 다운로드하여 반환하는 API
    """
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name="ap-northeast-2",
    )

    try:
        # S3에서 파일 가져오기
        response = s3_client.get_object(
            Bucket="yeonmubucket",  # S3 버킷 이름
            Key=file_key,  # S3 파일 경로
        )
        file_content = response["Body"].read()
        content_type = response["ContentType"]

        # HTTP 응답 생성
        response = HttpResponse(file_content, content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="{file_key.split("/")[-1]}"'
        return response

    except ClientError as e:
        # S3에서 파일을 찾을 수 없는 경우
        if e.response["Error"]["Code"] == "NoSuchKey":
            raise Http404("The requested file does not exist.")
        return Response({"error": "Failed to retrieve the file from S3."}, status=500)

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

def process_and_mask_image(image,denoised_image):
    """
    이미지에서 민감한 정보를 마스킹하여 반환합니다.
    """
    try:
        logger.debug("Starting process_and_mask_image")
        draw = ImageDraw.Draw(image)
        
        # OCR로 텍스트 추출
        logger.debug("Running OCR on the image")
        data = pytesseract.image_to_data(denoised_image, output_type=pytesseract.Output.DICT, lang="kor+eng")

        logger.debug(f"Extracted OCR data: {data}")
        
        for i in range(len(data['text'])):
                if '번' in data['text'][i] :
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    image_width = image.width
                    print(f"Found text '{data['text'][i]}' at position ({x}, {y}, {w}, {h})")  # 디버깅: 텍스트 위치 출력
                    draw.rectangle([(0, y - 10), (image_width, y + h + 10)], fill="black")
                    break  # 첫 번째 "번" 조건 만족 시 루프 종료
    
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
            pil_image = draw_bounding_box_colors_cv_link(cv_image)
        elif booking_page == "예스24":
            logger.debug("Using no-color bounding box for 예스24")
            pil_image = draw_bounding_box_colors_cv_24(cv_image)
        else:
            logger.debug("Using purple bounding box")
            pil_image = draw_bounding_box_colors_cv_park(cv_image)

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
    
# def draw_bounding_box_no_color_cv(cv_image, width_scale=4):
#     """좌석 이미지에 검정색 박스 그리기"""
#     try:
#         logger.debug("Starting draw_bounding_box_no_color_cv")
#         height, width, _ = cv_image.shape
#         gray_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
#         _, thresh_image = cv2.threshold(gray_image, 200, 255, cv2.THRESH_BINARY_INV)
#         contours, _ = cv2.findContours(thresh_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

#         pil_image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
#         draw = ImageDraw.Draw(pil_image)
#         for contour in contours:
#             x, y, w, h = cv2.boundingRect(contour)
#             if w > 5 and h > 5:
#                 box_x1 = max(0, x - w * (width_scale - 1) // 2)
#                 box_y1 = y
#                 box_x2 = min(width, x + w + w * (width_scale - 1) // 2)
#                 box_y2 = y + h
#                 draw.rectangle([box_x1, box_y1, box_x2, box_y2], outline="black", fill="black", width=3)
#         logger.debug("Bounding box (no color) drawn successfully")
#         return pil_image

#     except Exception as e:
#         logger.exception("Error in draw_bounding_box_no_color_cv")
#         return None
    
def draw_bounding_box_colors_cv_24(cv_image, width_scale=4):
    try:
        logger.debug("Starting draw_bounding_box_colors_cv")

        # Check the input image shape
        height, width, channels = cv_image.shape
        logger.debug(f"Image shape: height={height}, width={width}, channels={channels}")

        # Convert image to HSV color space
        hsv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        logger.debug("Converted image to HSV color space successfully")

        # Define HSV ranges for different colors
        color_ranges = [
            {"color": "blue", "lower": (50, 140, 140), "upper": (180, 255, 255)},
            {"color": "purple", "lower": (40, 70, 140), "upper": (130, 255, 255)},
            {"color": "red", "lower": (140, 0, 0), "upper": (255, 110, 100)},
            {"color": "yellow", "lower": (150, 150, 20), "upper": (255, 255, 150)}
        ]

        # Convert OpenCV image to PIL image for drawing
        pil_image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)

        # Iterate over color ranges
        for color_range in color_ranges:
            lower = color_range["lower"]
            upper = color_range["upper"]
            color_name = color_range["color"]

            # Create mask for the current color
            mask = cv2.inRange(hsv_image, lower, upper)
            logger.debug(f"Mask created for {color_name} with lower={lower}, upper={upper}")

            # Find contours in the mask
            contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            logger.debug(f"Number of {color_name} contours found: {len(contours)}")

            # If contours are found, draw bounding boxes and stop checking further colors
            if contours:
                for i, contour in enumerate(contours):
                    x, y, w, h = cv2.boundingRect(contour)
                    logger.debug(f"{color_name.capitalize()} Contour {i}: x={x}, y={y}, w={w}, h={h}")

                    box_x1 = max(0, x - w * (width_scale - 1) // 2)
                    box_y1 = y
                    box_x2 = min(width, x + w + w * (width_scale - 1) // 2)
                    box_y2 = y + h
                    logger.debug(f"Drawing rectangle for {color_name}: ({box_x1}, {box_y1}), ({box_x2}, {box_y2})")

                    draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill="black", width=3)

                logger.debug(f"Bounding boxes drawn for {color_name}")
                return pil_image

        # If no contours are found for any color, return the original image
        logger.warning("No contours found for any specified colors")
        return pil_image

    except Exception as e:
        logger.exception("Error in draw_bounding_box_colors_cv")
        return None
    
def draw_bounding_box_colors_cv_park(cv_image, width_scale=4):
    """좌석 이미지에서 보라색, 녹색, 파란색, 주황색 순으로 박스 그리기"""
    try:
        logger.debug("Starting draw_bounding_box_colors_cv_park")

        # Check the input image shape
        height, width, channels = cv_image.shape
        logger.debug(f"Image shape: height={height}, width={width}, channels={channels}")

        # Convert image to HSV color space
        hsv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        logger.debug("Converted image to HSV color space successfully")

        # Define HSV ranges for different colors
        color_ranges = [
            {"color": "purple", "lower": (120, 50, 50), "upper": (140, 255, 255)},
            {"color": "green", "lower": (40, 110, 0), "upper": (150, 230, 110)},
            {"color": "blue", "lower": (30, 100, 150), "upper": (170, 220, 255)},
            {"color": "orange", "lower": (170, 60, 20), "upper": (255, 200, 155)}
        ]

        # Convert OpenCV image to PIL image for drawing
        pil_image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)

        # Iterate over color ranges
        for color_range in color_ranges:
            lower = color_range["lower"]
            upper = color_range["upper"]
            color_name = color_range["color"]

            # Create mask for the current color
            mask = cv2.inRange(hsv_image, lower, upper)
            logger.debug(f"Mask created for {color_name} with lower={lower}, upper={upper}")

            # Find contours in the mask
            contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            logger.debug(f"Number of {color_name} contours found: {len(contours)}")

            # If contours are found, draw bounding boxes and stop checking further colors
            if contours:
                for i, contour in enumerate(contours):
                    x, y, w, h = cv2.boundingRect(contour)
                    logger.debug(f"{color_name.capitalize()} Contour {i}: x={x}, y={y}, w={w}, h={h}")

                    box_x1 = max(0, x - w * (width_scale - 1) // 2)
                    box_y1 = y
                    box_x2 = min(width, x + w + w * (width_scale - 1) // 2)
                    box_y2 = y + h
                    logger.debug(f"Drawing rectangle for {color_name}: ({box_x1}, {box_y1}), ({box_x2}, {box_y2})")

                    draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill="black", width=3)

                logger.debug(f"Bounding boxes drawn for {color_name}")
                return pil_image

        # If no contours are found for any color, return the original image
        logger.warning("No contours found for any specified colors")
        return pil_image

    except Exception as e:
        logger.exception("Error in draw_bounding_box_colors_cv")
        return None

def draw_bounding_box_colors_cv_link(cv_image, width_scale=4):
    """좌석 이미지에서 보라색, 녹색, 파란색, 주황색 순으로 박스 그리기"""
    try:
        logger.debug("Starting draw_bounding_box_colors_cv")

        # Check the input image shape
        height, width, channels = cv_image.shape
        logger.debug(f"Image shape: height={height}, width={width}, channels={channels}")

        # Convert image to HSV color space
        hsv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        logger.debug("Converted image to HSV color space successfully")

        # Define HSV ranges for different colors
        color_ranges = [
            {"color": "red", "lower": (120, 70, 0), "upper": (140, 80, 100)},
            {"color": "green", "lower": (0, 50, 40), "upper": (50, 190, 180)},
            {"color": "yellow", "lower": (170, 130, 0), "upper": (255, 240, 110)},
            {"color": "purple", "lower": (10, 0, 50), "upper": (150, 100, 170)}
        ]

        # Convert OpenCV image to PIL image for drawing
        pil_image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)

        # Iterate over color ranges
        for color_range in color_ranges:
            lower = color_range["lower"]
            upper = color_range["upper"]
            color_name = color_range["color"]

            # Create mask for the current color
            mask = cv2.inRange(hsv_image, lower, upper)
            logger.debug(f"Mask created for {color_name} with lower={lower}, upper={upper}")

            # Find contours in the mask
            contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            logger.debug(f"Number of {color_name} contours found: {len(contours)}")

            # If contours are found, draw bounding boxes and stop checking further colors
            if contours:
                for i, contour in enumerate(contours):
                    x, y, w, h = cv2.boundingRect(contour)
                    logger.debug(f"{color_name.capitalize()} Contour {i}: x={x}, y={y}, w={w}, h={h}")

                    box_x1 = max(0, x - w * (width_scale - 1) // 2)
                    box_y1 = y
                    box_x2 = min(width, x + w + w * (width_scale - 1) // 2)
                    box_y2 = y + h
                    logger.debug(f"Drawing rectangle for {color_name}: ({box_x1}, {box_y1}), ({box_x2}, {box_y2})")

                    draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill="black", width=3)

                logger.debug(f"Bounding boxes drawn for {color_name}")
                return pil_image

        # If no contours are found for any color, return the original image
        logger.warning("No contours found for any specified colors")
        return pil_image

    except Exception as e:
        logger.exception("Error in draw_bounding_box_colors_cv")
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
        uploaded_masked_file =request.FILES["maskedReservImage"]
        uploaded_masked_seat_file =request.FILES["maskedSeatImage"]
        is_transfer_value = request.data.get("isTransfer")

        # 문자열을 Boolean으로 변환
        if is_transfer_value in ["true", "True", True]:
            isTransfer = True
        elif is_transfer_value in ["false", "False", False]:
            isTransfer = False
        else:
            isTransfer = None  # 또는 적절한 기본값 설정

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
                isTransfer=isTransfer,
            )

            reserv_file_path = get_unique_file_path(uploaded_file, prefix=f"tickets/{ticket.id}")
            seat_file_path = get_unique_file_path(uploaded_seat_image, prefix=f"tickets/{ticket.id}")
            masked_reserv_file_path = get_unique_file_path(uploaded_masked_file, prefix=f"tickets/{ticket.id}")
            masked_seat_file_path= get_unique_file_path(uploaded_masked_seat_file, prefix=f"tickets/{ticket.id}")
            # 3) default_storage에 실제 저장
            reserv_path = default_storage.save(reserv_file_path, uploaded_file)
            seat_path = default_storage.save(seat_file_path, uploaded_seat_image)
            masked_reserv_path = default_storage.save(masked_reserv_file_path, uploaded_masked_file)
            masked_seat_path = default_storage.save(masked_seat_file_path, uploaded_masked_seat_file)

            # 4) DB 필드에 URL 저장
            ticket.uploaded_file_url = default_storage.url(reserv_path)
            ticket.uploaded_seat_image_url = default_storage.url(seat_path)
            ticket.masked_file_url = default_storage.url(masked_reserv_path)
            ticket.processed_seat_image_url = default_storage.url(masked_seat_path)
        
            # try:
            #     uploaded_file.seek(0)  # Ensure file pointer is at the beginning

            #     image = Image.open(BytesIO(uploaded_file.read()))
            #     logger.debug("Image loaded successfully for OCR")
            #     masked_image =process_and_mask_image(image)
                
            #     if masked_image:
            #         masked_name = f"ticket_{ticket.id}_masked.jpg"
            #         relative_path = f"tickets/{ticket.id}/{masked_name}"  # 상대 경로
            #         masked_url = default_storage.save(relative_path, File(masked_image))
            #         logger.debug(f"masked_url:{masked_url}")
            #         ticket.masked_file_url = f"https://yeonmubucket.s3.ap-northeast-2.amazonaws.com/tickets/{ticket.id}/{masked_name}"
            # except Exception as e:
            #     logger.exception("masked_File failed")
            #     return Response({"status": "error", "message": "masked_File failed"}, status=500)
            
            # try:
            #     uploaded_seat_image.seek(0)  # Ensure file pointer is at the beginning

            #     image = Image.open(uploaded_seat_image)
            #     logger.debug("Image loaded successfully for OCR")
            #     masked_seat_image =process_seat_image(image,ticket.booking_page)
                
            #     if masked_seat_image:
            #         masked_seat_name = f"ticket_{ticket.id}_processed.jpg"
            #         relative_path = f"tickets/{ticket.id}/{masked_seat_name}"  # 상대 경로
            #         masked_url = default_storage.save(relative_path, File(masked_seat_image))
            #         logger.debug(f"masked_url:{masked_url}")
            #         ticket.processed_seat_image_url =f"https://yeonmubucket.s3.ap-northeast-2.amazonaws.com/tickets/{ticket.id}/{masked_seat_name}"

            # except Exception as e:
            #     logger.exception("masked_File failed")
            #     return Response({"status": "error", "message": "masked_File failed"}, status=500)
        
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

        # 작성자가 아닌 경우 권한 없음
        if request.user != ticket_post.author:
            return Response(
                {"detail": "You are not authorized to edit this post."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 일반 텍스트 필드들만 업데이트
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

        # ─────────────────────────────────────────────────────
        # 1) 새 파일이 올라온 경우에만, 생성시와 동일한 로직 수행
        #    - reservImage(= uploaded_file) / seatImage(= uploaded_seat_image)
        # ─────────────────────────────────────────────────────

        if "uploaded_file" in request.FILES:
            uploaded_file = request.FILES["uploaded_file"]
            try:
                # 파일 경로 설정(중복 방지)
                reserv_file_path = get_unique_file_path(
                    uploaded_file, prefix=f"tickets/{ticket.id}"
                )
                # 실제 파일 저장
                reserv_path = default_storage.save(reserv_file_path, uploaded_file)
                # DB 필드에 URL 저장
                ticket.uploaded_file_url = default_storage.url(reserv_path)

                # masking, OCR 등 작업
                uploaded_file.seek(0)  # 파일 포인터를 맨 앞으로
                image = Image.open(BytesIO(uploaded_file.read()))
                logger.debug("Image loaded successfully for OCR (reservImage)")
                masked_image = process_and_mask_image(image)

                if masked_image:
                    masked_name = f"ticket_{ticket.id}_masked.jpg"
                    relative_path = f"tickets/{ticket.id}/{masked_name}"
                    masked_url = default_storage.save(relative_path, File(masked_image))
                    logger.debug(f"masked_url: {masked_url}")
                    ticket.masked_file_url = (
                        f"https://yeonmubucket.s3.ap-northeast-2.amazonaws.com/"
                        f"tickets/{ticket.id}/{masked_name}"
                    )
            except Exception as e:
                logger.exception("masked_File failed")
                return Response(
                    {"status": "error", "message": "reservImage masking/processing failed"},
                    status=500,
                )

        if "uploaded_seat_image" in request.FILES:
            uploaded_seat_image = request.FILES["uploaded_seat_image"]
            try:
                # 파일 경로 설정(중복 방지)
                seat_file_path = get_unique_file_path(
                    uploaded_seat_image, prefix=f"tickets/{ticket.id}"
                )
                # 실제 파일 저장
                seat_path = default_storage.save(seat_file_path, uploaded_seat_image)
                # DB 필드에 URL 저장
                ticket.uploaded_seat_image_url = default_storage.url(seat_path)

                # masking, OCR 등 작업
                uploaded_seat_image.seek(0)  # 파일 포인터를 맨 앞으로
                image = Image.open(uploaded_seat_image)
                logger.debug("Image loaded successfully for OCR (seatImage)")
                # process_seat_image 함수에 booking_page 같은 정보가 필요하다면 ticket.booking_page를 인자로
                masked_seat_image = process_seat_image(image, ticket.booking_page)

                if masked_seat_image:
                    masked_seat_name = f"ticket_{ticket.id}_processed.jpg"
                    relative_path = f"tickets/{ticket.id}/{masked_seat_name}"
                    masked_url = default_storage.save(relative_path, File(masked_seat_image))
                    logger.debug(f"masked_url: {masked_url}")
                    ticket.processed_seat_image_url = (
                        f"https://yeonmubucket.s3.ap-northeast-2.amazonaws.com/"
                        f"tickets/{ticket.id}/{masked_seat_name}"
                    )
            except Exception as e:
                logger.exception("masked_File failed")
                return Response(
                    {"status": "error", "message": "seatImage masking/processing failed"},
                    status=500,
                )

        # DB에 최종 저장
        try:
            ticket.save()
            ticket_post.save()
        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = TicketPostSerializer(ticket_post, context={"request": request})
        response_data = serializer.data

        return Response(response_data, status=status.HTTP_201_CREATED)
    
class TransferListView(APIView):
    @swagger_auto_schema(
        operation_id="양도 티켓 목록 조회",
        operation_description="사용자가 양도한 티켓 목록을 조회합니다.",
        responses={200: TicketSerializer(many=True), 404: "Not Found", 400: "Bad Request"},
    )
    def get(self, request):
        user = request.user
        # isTransfer=True 인 티켓만 필터
        transfer_list = Ticket.objects.filter(
            owner=user,
            isTransfer=True,  # 양도글
        ).order_by('-id')

        if not transfer_list.exists():
            return Response({"detail": "No transferred tickets found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = TicketSerializer(transfer_list, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class ExchangeListView(APIView):
    @swagger_auto_schema(
        operation_id="교환 티켓 목록 조회",
        operation_description="사용자가 교환한 티켓 목록을 조회합니다.",
        responses={200: ExchangeSerializer(many=True), 404: "Not Found", 400: "Bad Request"},
    )
    def get(self, request):
        user = request.user

        # 교환 티켓 목록 필터링
        exchange_list = Exchange.objects.filter(
            Q(owner=user) | Q(transferee=user),  # owner가 user이거나 transferee가 user인 경우                  # 그리고 isTransfer가 False인 경우
        ).order_by('-id')
        
        transfer_list = Ticket.objects.filter(
            owner=user,
            isTransfer=False,
            transferee__isnull=True  # transferee가 비어 있는 경우
        ).order_by('-id')
        

        # 교환 데이터가 없을 경우
        if not exchange_list.exists():
            return Response({"detail": "No exchanged tickets found."}, status=status.HTTP_404_NOT_FOUND)

        # ExchangeSerializer를 사용하여 데이터를 직렬화
        exchange_serializer = ExchangeSerializer(exchange_list, many=True, context={'request': request})
        transfer_serializer = TicketSerializer(transfer_list, many=True, context={'request': request})

        # 직렬화된 데이터를 반환
        return Response({
            "exchanges": exchange_serializer.data,
            "available_tickets": transfer_serializer.data
        }, status=status.HTTP_200_OK)


class ReceivedListView(APIView):
    @swagger_auto_schema(
        operation_id="양수 티켓 목록 조회",
        operation_description="사용자가 양수받은 티켓 목록을 조회합니다.",
        responses={200: TicketSerializer(many=True), 404: "Not Found", 400: "Bad Request"},
    )
    def get(self, request):
        user = request.user
        received_list = Ticket.objects.filter(
            transferee=user,
            isTransfer=True,
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
        if 'reservImage' not in request.FILES or 'seatImage' not in request.FILES:
            logger.debug(f"Uploaded files: {request.FILES.keys()}")
            return Response({"status": "error", "message": "Both files (reservImage, seatImage) are required."}, status=400)

        reserv_image = request.FILES['reservImage']
        seat_image = request.FILES['seatImage']

        try:
            reserv_image.seek(0)  # Ensure file pointer is at the beginning
            logger.debug("Starting OCR processing for reservImage")

            reservimage = Image.open(BytesIO(reserv_image.read()))
            logger.debug("reservImage opened successfully for OCR")
            image_arr = np.array(reservimage)

            gray_image = cv2.cvtColor(image_arr, cv2.COLOR_BGR2GRAY)
            binary_image = cv2.adaptiveThreshold(gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            denoised_image = cv2.medianBlur(binary_image, 3)

            # Single OCR extraction
            extracted_text = pytesseract.image_to_string(denoised_image, lang="kor+eng")
            logger.debug(f"Extracted text: {extracted_text}")

        except Exception as e:
            logger.exception("OCR processing failed")
            return Response({"status": "error", "message": "OCR failed."}, status=500)

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

        try:
            masked_image = process_and_mask_image(reservimage,denoised_image)
            if masked_image:
                masked_image_base64 = base64.b64encode(masked_image.getvalue()).decode('utf-8')
                response_data['masked_image'] = f"data:image/jpeg;base64,{masked_image_base64}"
            else:
                logger.error("masked_image is None.")

        except Exception as e:
            logger.exception("Masked image processing failed")
            return Response({"status": "error", "message": "Masked image processing failed"}, status=500)

        try:
            seat_image.seek(0)
            seatimage_pil = Image.open(seat_image)
            logger.debug("seatImage opened successfully")

            masked_seat_image = process_seat_image(seatimage_pil, keyword)
            if masked_seat_image:
                masked_seat_image_base64 = base64.b64encode(masked_seat_image.getvalue()).decode('utf-8')
                response_data['masked_seat_image'] = f"data:image/jpeg;base64,{masked_seat_image_base64}"
            else:
                logger.error("masked_seat_image is None.")

        except Exception as e:
            logger.exception("Masked seat image processing failed")
            return Response({"status": "error", "message": "Masked seat image processing failed"}, status=500)

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
        seat_number = extract_line_with_yeol_and_beon_link(extracted_text)
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
    pattern = r'([가-힣]*결제금액)\s*(\d{1,3}(,\d{3})*)\s*원'
    match = re.search(pattern, text)

    if not match:
        return ""

    return match.group(2).replace(",", "")  # 숫자만 반환

def extract_line_after_at_link(text):
    # '장소' 이후의 모든 텍스트 추출
    pattern = r'장소\s*(.*)'
    match = re.search(pattern, text)

    if not match:
        return ""

    # '장소' 뒤의 내용을 공백 없이 추출
    location_info = match.group(1).strip()

    return location_info
    
def extract_line_with_yeol_and_beon_link(text):
    # '좌석정보' 바로 다음 줄 추출
    pattern = r'좌석정보\s*\n([^\n]*)'  # '좌석정보' 이후의 줄을 캡처
    match = re.search(pattern, text)

    if not match:
        return ""  # '좌석정보' 다음 줄이 없을 경우 빈 문자열 반환

    next_line = match.group(1).strip()  # '좌석정보' 다음 줄의 텍스트 추출
    return next_line

def extract_discount_info_link(text):
    # 줄 단위로 텍스트를 분리
    lines = text.splitlines()

    # '할인'이라는 단어가 포함된 첫 번째 줄을 탐색
    for line in lines:
        if "할인" in line:
            # '할인' 단어가 포함된 텍스트를 추출
            pattern = r'([가-힣\s]*할인)'  # 한글 및 공백 포함 '재관람 할인' 등 전체 매칭
            match = re.search(pattern, line)
            if match:
                return match.group(1).strip()  # '재관람 할인' 반환

    # '할인' 단어가 없으면 빈 문자열 반환
    return ""

def process_interpark_data(extracted_text):
    try:
        reservation_status = check_reservation_status_park(extracted_text)
        date_info = extract_viewing_info_park(extracted_text)
        ticket_number = extract_ticket_number_park(extracted_text)
        cast_info = extract_cast_park(extracted_text)
        total_amount = extract_total_amount_park(extracted_text)
        price_grade = extract_price_grade_park(extracted_text)
        seat_number = extract_seat_number_park(extracted_text)
        place = extract_line_after_at_park(extracted_text)

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

def check_reservation_status_park(text):
    # Extracts reservation status from the text
    pattern = r'예매상태\s*(.*)'
    match = re.search(pattern, text)
    if not match:
        return ""
    return match.group(1).strip() if match else ""

def extract_viewing_info_park(text):
    # Extracts viewing information (date and time) from the text
    date_time_pattern = r'관람일시\s*(\d{4})\.(\d{2})\.(\d{2})\(\s*([가-힣]{1})\s*\)\s*(\d{2}):(\d{2})'
    match = re.search(date_time_pattern, text)
    if not match:
        return {}
    year, month, day, day_of_week, hour, minute = match.groups()
    return {
        '관람년도': year,
        '관람월': month,
        '관람일': day,
        '관람요일': day_of_week,
        '시간': f"{hour}:{minute}"
    }

def extract_ticket_number_park(text):
    # Extracts the ticket number from the text
    ticket_number_pattern = r'예매번호\s*([\dA-Za-z]+)'
    match = re.search(ticket_number_pattern, text)
    if not match:
        return {}
    return f"T{match.group(1)[-10:]}" if match else ""

def extract_cast_park(text):
    # Extracts main cast information from the text and retrieves the last three characters of each line
    cast_pattern = r'출연진\s*(.*?)\s*수령'
    match = re.search(cast_pattern, text, re.DOTALL)
    if not match:
        return []
    cast_lines = match.group(1).splitlines()
    cast_names = []
    for line in cast_lines:
        clean_line = line.strip()
        if re.search(r'[가-힣]{2,}', clean_line):  # Ensure the line contains at least 2 Korean characters
            last_three_chars = clean_line[-3:]  # Extract the last three characters
            cast_names.append(last_three_chars)
    return cast_names

def extract_total_amount_park(text):
    # Extracts the total payment amount
    amount_pattern = r'결제금액\s*([\d,]+)\s*원'
    match = re.search(amount_pattern, text)
    if not match:
        return ""
    return match.group(1) if match else ""

def extract_price_grade_park(text):
    # Extracts all text after "가격등급" until the end of the line
    price_grade_pattern = r'가격등급\s*(.*)'
    match = re.search(price_grade_pattern, text)
    if not match:
        return ""
    return match.group(1).strip() if match else ""

def extract_seat_number_park(text):
    # Extracts the seat number
    seat_number_pattern = r'좌석번호\s*([\dA-Za-z]+)'
    match = re.search(seat_number_pattern, text)
    if not match:
        return ""
    return match.group(1) if match else ""

def extract_line_after_at_park(text):
    # Extracts the line after '@' and removes the trailing '>'
    at_pattern = r'@\s*(.*)'
    match = re.search(at_pattern, text)
    if not match:
        return ""
    line_without_symbols = match.group(1).strip().rstrip('>')
    return line_without_symbols

def process_yes24_data(extracted_text):
    try:
        # 예스24 관련 예매 상태 및 필요한 정보 추출 처리
        reservation_status = check_reservation_status_yes24(extracted_text)
        date_info = extract_viewing_info_yes24(extracted_text)
        total_amount = extract_total_amount_yes24(extracted_text)
        price_grade = extract_price_grade_yes24(extracted_text)
        seat_number = extract_seat_number_yes24(extracted_text)
        place = extract_line_after_at_yes24(extracted_text)

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
# 예스24 관련 예매 상태 확인 함수 정의
def check_reservation_status_yes24(text):
    """
    '상태'와 그 옆의 텍스트가 예매, 취소 등으로 표현되어 있을 때 추출한다.
    예) 상태              예매
    """
    # '상태' 다음에 오는 글자(공백 포함 x)를 찾기
    pattern = r'상태\s+([\w가-힣]+)'
    match = re.search(pattern, text)
    if not match:
        return ""
    return match.group(1).strip()

# 예스24 관련 날짜 정보 추출 함수
def extract_viewing_info_yes24(text):
    """
    예) 관람일시        2024.10.03 14:00
    -> {'관람년도': '2024', '관람월': '10', '관람일': '03', '시간': '14:00'}
    """
    # 2024.10.03 14:00 형태로 파싱
    pattern = r'관람일시\s+(\d{4})\.(\d{2})\.(\d{2})\s+(\d{2}):(\d{2})'
    match = re.search(pattern, text)
    if not match:
        return {}

    year, month, day, hour, minute = match.groups()
    return {
        '관람년도': year,
        '관람월': month,
        '관람일': day,
        '시간': f"{hour}:{minute}"
    }

# 예스24 관련 총 결제 금액 추출 함수
def extract_total_amount_yes24(text):
    """
    예) 종 결제금액       51,500원
    -> 51500  (문자열)
    """
    # '종 결제금액' 뒤에 금액이 나오는 형태
    pattern = r'(종|총)\s*결제금액\s+([\d,]+)원'
    match = re.search(pattern, text)
    if not match:
        return ""
    # 쉼표 제거 후 반환
    return match.group(2).replace(",", "")

# 예스24 관련 할인 금액 추출 함수
def extract_price_grade_yes24(text):
    """
    좌석정보 아래 또는 티켓금액 위에 위치한 할인 정보를 추출합니다.
    """
    # 정규식: 좌석정보 바로 아래 또는 티켓금액 바로 위의 '할인' 정보를 탐지
    pattern1 = r'할인금액\s*[\d,]+원\((.*?)\)'
    match1 = re.search(pattern1, text)
    if match1:
        return match1.group(1).strip()

    # (2) '할인' 뒤에 직접 할인명이 기재된 경우
    pattern2 = r'할인\s+([^\n]+)'
    match2 = re.search(pattern2, text)
    if match2:
        return match2.group(1).strip()

    return ""

# 예스24 관련 좌석 번호 추출 함수
def extract_seat_number_yes24(text):
    # '전체선택' 이후의 텍스트에서 '좌석정보' 줄을 찾음
    pattern = r'전체선택\s+좌석정보\s+([^\n]*)'
    match = re.search(pattern, text)
    if not match:
        return ""

    # '열'과 '번'이 모두 포함된 경우만 반환
    seat_info = match.group(1).strip()
    return seat_info

    return ""

# 예스24 관련 극장명 추출 함수
def extract_line_after_at_yes24(text):
    pattern = r'\]\s*\n\s*(.*?)(?:\*|$)'
    match = re.search(pattern, text)
    if not match:
        return ""

    # 추출된 극장명 양끝 공백 제거
    extracted_text = match.group(1).strip()
    return extracted_text


from TwitterAPI import TwitterAPI

# Twitter API Credentials
CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

@csrf_exempt
def post_tweet(request):
    """
    Post a tweet with an optional image using TwitterAPI.
    """
    try:
        # 인증 정보 유효성 검사
        if not all([CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET]):
            raise Exception("Missing Twitter API authentication parameters")

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

        
        # 트윗 작성
        params = {"status": tweet_content}

        response = api.request("statuses/update", params)
        if response.status_code not in [200, 201]:
            return JsonResponse(
                {"message": "트윗 게시 중 오류가 발생했습니다.", "error": response.text},
                status=response.status_code,
            )

        return JsonResponse(
            {"message": "트윗이 성공적으로 게시되었습니다.", "tweet": response.json()}
        )

    except json.JSONDecodeError:
        return JsonResponse({"message": "JSON 형식이 잘못되었습니다."}, status=400)
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