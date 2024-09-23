from rest_framework import serializers

from user.request_serializers import SignInRequestSerializer


class TicketListRequestSerializer(serializers.Serializer):
    owner = SignInRequestSerializer()
    title = serializers.CharField()
    description = serializers.CharField()  # 티켓 설명
    date = serializers.DateField()  # 티켓 날짜
    seat = serializers.CharField(max_length=50)  # 좌석 정보
    booking_details = serializers.CharField(max_length=100)  # 할인 정보
    price = serializers.DecimalField(max_digits=10, decimal_places=2)  # 가격
    casting = serializers.CharField(max_length=100)  # 캐스팅 정보
    uploaded_file = serializers.FileField(required=True, allow_null=True)  # 파일 업로드

class TicketDetailRequestSerializer(serializers.Serializer):
    owner = SignInRequestSerializer()
    title = serializers.CharField()
    description = serializers.CharField()  # 티켓 설명
    date = serializers.DateField()  # 티켓 날짜
    seat = serializers.CharField(max_length=50)  # 좌석 정보
    booking_details = serializers.CharField(max_length=100)  # 할인 정보
    price = serializers.DecimalField(max_digits=10, decimal_places=2)  # 가격
    casting = serializers.CharField(max_length=100)  # 캐스팅 정보
    uploaded_file = serializers.FileField(required=True, allow_null=True)  # 파일 업로드