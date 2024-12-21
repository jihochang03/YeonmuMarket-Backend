from rest_framework import serializers
from user.request_serializers import SignInRequestSerializer

class TicketPostListRequestSerializer(serializers.Serializer):
    owner = SignInRequestSerializer()
    transferee = SignInRequestSerializer(required=False, allow_null=True)  # transferee 추가
    title = serializers.CharField()
    description = serializers.CharField()  # 티켓 설명
    date = serializers.DateField()  # 티켓 날짜
    seat = serializers.CharField(max_length=50)  # 좌석 정보
    booking_details = serializers.CharField(max_length=100)  # 할인 정보
    booking_page =serializers.CharField(max_length=100) 
    status=serializers.CharField(max_length=100) 
    price = serializers.DecimalField(max_digits=10, decimal_places=2)  # 가격
    casting = serializers.CharField(max_length=100)  # 캐스팅 정보
    uploaded_file_url = serializers.FileField(required=True, allow_null=False)  # 예매내역서 파일 업로드
    uploaded_seat_image_url = serializers.FileField(required=True, allow_null=False)  # 좌석 사진 파일 업로드

class TicketPostDetailRequestSerializer(serializers.Serializer):
    owner = SignInRequestSerializer()
    transferee = SignInRequestSerializer(required=False, allow_null=True)  # transferee 추가
    title = serializers.CharField()
    description = serializers.CharField()  # 티켓 설명
    date = serializers.DateField()  # 티켓 날짜
    seat = serializers.CharField(max_length=50)  # 좌석 정보
    booking_details = serializers.CharField(max_length=100)  # 할인 정보
    booking_page =serializers.CharField(max_length=100) 
    status=serializers.CharField(max_length=100) 
    price = serializers.DecimalField(max_digits=10, decimal_places=2)  # 가격
    casting = serializers.CharField(max_length=100)  # 캐스팅 정보
    uploaded_file_url = serializers.FileField(required=False, allow_null=True)  # 예매내역서 파일 (옵션)
    uploaded_seat_image_url= serializers.FileField(required=False, allow_null=True)  # 좌석 사진 파일 (옵션)
