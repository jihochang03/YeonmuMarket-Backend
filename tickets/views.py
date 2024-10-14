from django.shortcuts import render
from rest_framework.views import APIView
from drf_yasg import openapi
from rest_framework import status
from rest_framework.response import Response
from .models import Ticket, TicketPost
from .serializers import TicketSerializer, TicketPostSerializer
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Q
from .request_serializers import TicketPostListRequestSerializer, TicketPostDetailRequestSerializer
from user.models import User
from user.request_serializers import SignInRequestSerializer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from PIL import Image
import pytesseract
import re
import os
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from conversations.models import Conversation  # Import Conversation model
from user.models import UserProfile
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

class TicketPostListView(APIView):
    @swagger_auto_schema(
        operation_id="티켓 양도글 생성",
        operation_description="티켓 양도글을 생성합니다.",
        request_body=TicketPostListRequestSerializer,
        responses={201: TicketPostSerializer, 404: "Not Found", 400: "Bad Request"},
    )
    def post(self, request):
        user = request.user
        print(f"-------- User: {user}" )  # 유저 정보 출력
        if user.is_anonymous:
            return Response({"detail": "인증되지 않은 사용자입니다. 로그인 후 시도해주세요."}, status=status.HTTP_401_UNAUTHORIZED)
        print(f"Received user: {user}")  # 유저 정보 출력
        print("Received data:", request.data)  # 요청 데이터 출력
        print("Received files:", request.FILES)  # 파일 데이터 출력

        title = request.data.get("title")
        date = request.data.get("date")
        seat = request.data.get("seat")
        booking_details = request.data.get("booking_details")
        price = request.data.get("price")
        casting = request.data.get("casting")
        uploaded_file = request.FILES.get("uploaded_file")
        uploaded_seat_image = request.FILES.get("uploaded_seat_image")
        keyword = request.data.get("keyword")
        phone_last_digits = request.data.get("phone_last_digits")

        if not uploaded_file or not uploaded_seat_image:
            print("No files received or file upload failed.")
        else:
            print(f"Uploaded file: {uploaded_file.name}")
            print(f"Uploaded seat image: {uploaded_seat_image.name}")

        # 필수 필드가 있는지 확인
        if not title or not date or not seat or not price or not casting:
            print("필수 필드가 누락되었습니다.")  # 디버깅: 필수 필드 누락 여부 확인
            return Response({"detail": "필수 항목이 누락되었습니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Ticket 객체 생성
            print("Creating Ticket object...")  # 디버깅: Ticket 객체 생성 전 로그
            ticket = Ticket.objects.create(
                title=title,
                date=date,
                seat=seat,
                booking_details=booking_details,
                price=price,
                casting=casting,
                uploaded_file=uploaded_file,
                uploaded_seat_image=uploaded_seat_image,
                phone_last_digits=phone_last_digits,  # 전화번호 마지막 4자리 저장
                owner=user,  # 현재 로그인된 사용자
            )
            print("Ticket created:", ticket)  # 디버깅: 생성된 티켓 정보 출력

            if uploaded_seat_image:
                print("Saving uploaded seat image...")  # 디버깅: 이미지 저장 전 로그
                ticket.save(keyword=keyword)

            # 티켓과 관련된 대화 생성
            print("Creating Conversation object...")  # 디버깅: Conversation 생성 전 로그
            conversation = Conversation.objects.create(
                ticket=ticket,
                owner=user,
                transferee=None  # 양도자가 아직 없음
            )
            print("Conversation created:", conversation)  # 디버깅: 생성된 대화 정보 출력

            # TicketPost 객체 생성
            print("Creating TicketPost object...")  # 디버깅: TicketPost 생성 전 로그
            ticket_post = TicketPost.objects.create(
                ticket=ticket,
                author=user
            )
            ticket_post.save()
            print("TicketPost created:", ticket_post)  # 디버깅: 생성된 TicketPost 정보 출력

        except Exception as e:
            print(f"오류 발생: {str(e)}")  # 디버깅: 발생한 오류 출력
            return Response({"detail": f"오류 발생: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        # 성공적으로 생성된 경우의 응답
        serializer = TicketPostSerializer(ticket_post)
        print("Serialized data:", serializer.data)  # 디버깅: 응답으로 보낼 데이터 출력
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TicketPostDetailView(APIView):
    @swagger_auto_schema(
        operation_id="양도글 상세 조회",
        operation_description="양도글 1개의 상세 정보를 조회합니다.",
        responses={200: TicketPostSerializer, 400: "Bad Request"},
    )
    def get(self, request):
        try:
            ticket_post_id = request.GET.get("ticket_post_id")
            ticket_post = TicketPost.objects.get(id=ticket_post_id)
        except TicketPost.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = TicketPostSerializer(instance=ticket_post)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="티켓 양도글 삭제",
        operation_description="티켓 양도글을 삭제합니다.",
        request_body=SignInRequestSerializer,
        responses={204: "No Content", 404: "Not Found", 400: "Bad Request"},
    )
    def delete(self, request, ticket_post_id):
        try:
            ticket_post = TicketPost.objects.get(id=ticket_post_id)
        except Ticket.DoesNotExist:
            return Response({"detail": "Post Not found."}, status=status.HTTP_404_NOT_FOUND)

        author_info = request.data
        if not author_info:
            return Response({"detail": "author field missing."}, status=status.HTTP_400_BAD_REQUEST)

        username = author_info.get("username")
        password = author_info.get("password")

        try:
            author = User.objects.get(username=username)
            if not author.check_password(password):
                return Response({"detail": "Password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
            if ticket_post.author != author:
                return Response({"detail": "You are not the author of this post."}, status=status.HTTP_403_FORBIDDEN)

        except User.DoesNotExist:
            return Response({"detail": "User Not found."}, status=status.HTTP_404_NOT_FOUND)

        # ticket - ticket_post를 one-to-one으로 한다면 ticket.delete()
        # ticket -ticket_post를 one-to-many로 한다면 ticket_post.delete() 
        ticket_post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_id="티켓 양도글 수정",
        operation_description="티켓 양도글을 수정합니다.",
        request_body=TicketPostDetailRequestSerializer,
        responses={200: TicketPostSerializer, 404: "Not Found", 400: "Bad Request"},
    )
    def put(self, request, ticket_post_id):
        try:
            ticket_post = TicketPost.objects.get(id=ticket_post_id)
        except TicketPost.DoesNotExist:
            return Response({"detail": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        author_info = request.data.get("owner")
        if not author_info:
            return Response({"detail": "author field missing."}, status=status.HTTP_400_BAD_REQUEST)

        username = author_info.get("username")
        password = author_info.get("password")

        try:
            author = User.objects.get(username=username)
            if not author.check_password(password):
                return Response({"detail": "Password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
            if ticket_post.author != author:
                return Response({"detail": "You are not the author of this post."}, status=status.HTTP_403_FORBIDDEN)

        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # 필드 업데이트
        title = request.data.get("title")
        date = request.data.get("date")
        seat = request.data.get("seat")
        booking_details = request.data.get("booking_details")
        price = request.data.get("price")
        casting = request.data.get("casting")
        uploaded_file = request.FILES.get("uploaded_file")
        uploaded_seat_image = request.FILES.get("uploaded_seat_image")
        

        if not title or not date or not seat or not price or not casting:
            return Response({"detail": "Required fields missing."}, status=status.HTTP_400_BAD_REQUEST)

        # 업데이트된 필드 적용
        ticket_post.title = title
        ticket_post.date = date
        ticket_post.seat = seat
        ticket_post.booking_details = booking_details
        ticket_post.price = price
        ticket_post.casting = casting
        ticket_post.uploaded_file = uploaded_file
        ticket_post.uploaded_seat_image = uploaded_seat_image

        ticket_post.save(keyword=request.data.get('keyword', None))  # 좌석 이미지 처리

        serializer = TicketPostSerializer(instance=ticket_post)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TransferListView(APIView):
    @swagger_auto_schema(
        operation_id="양도 티켓 목록 조회",
        operation_description="사용자가 양도한 티켓 목록을 조회합니다.",
        responses={200: TicketSerializer(many=True), 404: "Not Found", 400: "Bad Request"},
    )
    def get(self, request):
        user = request.user
        transfer_list = Ticket.objects.filter(
            owner=user, status__in=['transfer_pending', 'transfer_completed']
        ).order_by('-id')

        if not transfer_list.exists():
            return Response({"detail": "No transferred tickets found."}, status=status.HTTP_404_NOT_FOUND)

        transfer_serializer = TicketSerializer(transfer_list, many=True)
        print(transfer_serializer.data)
        return Response(transfer_serializer.data, status=status.HTTP_200_OK)


class ReceivedListView(APIView):
    @swagger_auto_schema(
        operation_id="양수 티켓 목록 조회",
        operation_description="사용자가 양수받은 티켓 목록을 조회합니다.",
        responses={200: TicketSerializer(many=True), 404: "Not Found", 400: "Bad Request"},
    )
    def get(self, request):
        user = request.user
        received_list = Ticket.objects.filter(
            transferee=user, status__in=['transfer_pending', 'transfer_completed']
        ).order_by('-id')

        if not received_list.exists():
            return Response({"detail": "No received tickets found."}, status=status.HTTP_404_NOT_FOUND)

        received_serializer = TicketSerializer(received_list, many=True)
        return Response(received_serializer.data, status=status.HTTP_200_OK)
    
import logging

logger = logging.getLogger(__name__)
    
# Tesseract 경로 설정 (윈도우 경로 설정)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

@swagger_auto_schema(
    method='post',
    operation_description="JPG 파일과 입력어(인터파크)를 받아 텍스트를 분석하고 예매 정보를 반환합니다.",
    manual_parameters=[
        openapi.Parameter('file', openapi.IN_FORM, description="이미지 파일 (JPG, PNG 형식)", type=openapi.TYPE_FILE),
        openapi.Parameter('keyword', openapi.IN_FORM, description="입력어 (인터파크, 예스24, 티켓링크)", type=openapi.TYPE_STRING),
    ],
    responses={200: '성공 시 예매 정보를 반환합니다.'}
)
@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser])
def process_image(request):
    try:
        # Ensure keyword and both files are present
        keyword = request.POST.get('keyword', '').strip()
        print(keyword)

        if 'reservImage' not in request.FILES or 'seatImage' not in request.FILES:
            return Response({"status": "error", "message": "Both files are required."}, status=400)

        # Handle reservation image
        reserv_image = request.FILES['reservImage']
        reserv_file_path = default_storage.save(f'uploads/{reserv_image.name}', reserv_image)
        reserv_file_full_path = os.path.join(default_storage.location, reserv_file_path)

        # Handle seat image
        seat_image = request.FILES['seatImage']
        seat_file_path = default_storage.save(f'uploads/{seat_image.name}', seat_image)
        seat_file_full_path = os.path.join(default_storage.location, seat_file_path)

        # Process reservation image using pytesseract
        image = Image.open(reserv_file_full_path)
        extracted_text = pytesseract.image_to_string(image, lang="kor+eng")

        # Depending on the keyword, process the image data
        if keyword == '인터파크':
            # Process Interpark related data
            response_data = process_interpark_data(extracted_text)
            print(response_data)
            return JsonResponse(response_data, status=200)
        elif keyword == '예스24':
            # Process Yes24 related data
            response_data = process_yes24_data(extracted_text)
            print(response_data)
            if not isinstance(response_data, dict):  # Ensure it's a dictionary
                print("Invalid response_data format")
            return JsonResponse(response_data, status=200, safe=False)
        elif keyword == '티켓링크':
            # Process Ticketlink related data
            response_data = process_link_data
            if not isinstance(response_data, dict):  # Ensure it's a dictionary
                print("Invalid response_data format")
            return JsonResponse(response_data, status=200)
        else:
            return Response({"status": "error", "message": "Invalid keyword."}, status=400)

    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=500)

def process_link_data(extracted_text):
    try:
        reservation_status = check_reservation_status(extracted_text)
        date_info = extract_viewing_info_link(extracted_text)
        ticket_number = extract_ticket_number_link(extracted_text)
        # cast_info = extract_cast(extracted_text)
        total_amount = extract_total_amount(extracted_text)
        price_grade = extract_discount_info(extracted_text)
        seat_number = extract_line_with_yeol_and_beon(extracted_text)
        place = extract_line_after_at_link(extracted_text)

        # 딕셔너리로 반환
        return {
            "status": "success",
            "reservation_status": reservation_status,
            "date_info": date_info,
            "ticket_number": ticket_number,
            # "cast_info": cast_info,
            "total_amount": total_amount,
            "price_grade": price_grade,
            "seat_number": seat_number,
            "place": place,
        }
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    
def extract_line_with_yeol_and_beon(text):
    # 텍스트를 줄 단위로 분리
    lines = text.splitlines()

    # '열'과 '번'이 동시에 있는 줄 찾기
    for line in lines:
        if '열' in line and '번' in line:
            # 공백을 제거하고 반환
            return line.replace(' ', '')

    return ""  # 정보를 찾지 못했을 때 빈 문자열 반환    

def extract_line_after_at_link(text):
    # '장 소' 이후의 모든 글자를 추출하는 정규식
    pattern = r'장 소\s*(.*)'
    match = re.search(pattern, text)

    if not match:
        return ""

    # '장 소' 뒤의 내용을 공백 없이 추출
    location_info = match.group(1).replace(' ', '')

    return location_info

def extract_ticket_number_link(text):
    ticket_number_pattern = r'예 매 번 호\s*([A-Za-z0-9]+)'
    match = re.search(ticket_number_pattern, text)

    if not match:
        return ""

    ticket_number = match.group(1)[-10:]
    result = f"{ticket_number}"
    return result

def extract_viewing_info_link(text):
    # '관 람 일 시' 부분에서 날짜와 시간 추출 (YYYY.MM.DD (요일) HH:MM 형식)
    date_time_pattern = r'관 람 일 시\s*(\d{4})\.(\d{2})\.(\d{2})\(\s*(\w{1})\s*\)\s*(\d{2}):(\d{2})'
    match = re.search(date_time_pattern, text)

    if not match:
        return "관람 일시 정보를 찾을 수 없습니다."

    # 추출된 값을 변수에 저장
    year, month, day, day_of_week, hour, minute = match.groups()

    # 결과를 딕셔너리로 반환
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

def extract_discount_info(text):
    # 텍스트를 줄 단위로 분리
    lines = text.splitlines()

    # '결 제 정 보'가 나오는 줄의 인덱스 찾기
    for i, line in enumerate(lines):
        if '결 제 정 보' in line:
            # '결 제 정 보' 이전의 가장 가까운 줄에서 가격을 찾음
            for j in range(i-1, -1, -1):  # 위쪽 줄들을 탐색
                # 가격(숫자, 천 단위 콤마, '원')이 포함된 줄 찾기
                match = re.search(r'(\d{1,3}(,\d{3})*)\s*원', lines[j])
                if match:
                    # 금액 전의 글자들을 공백 없이 추출
                    discount_info = lines[j][:match.start()].replace(' ', '')
                    return discount_info

    return ""  # 정보를 찾지 못했을 때 빈 문자열 반환

def process_interpark_data(extracted_text):
    try:
        reservation_status = check_reservation_status(extracted_text)
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
def check_reservation_status(text):
    status_pattern = r'예 매 상 태\s*(.*)'
    match = re.search(status_pattern, text)
    
    # if not match:
    #     raise ValueError("예매 상태 정보를 찾을 수 없습니다.")
    
    reservation_status = match.group(1).strip()
    
    # if reservation_status != "예 매 완 료":
    #     raise ValueError(f"오류: 예매 상태가 '예 매 완 료'가 아닙니다. 현재 상태: {reservation_status}")
    
    return reservation_status

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


