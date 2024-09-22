from django.shortcuts import render

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Point
from .serializers import PointSerializer

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .request_serializers import PointRequestSerializer

# Create your views here.
class PointListView(APIView):
    @swagger_auto_schema(
        operation_id="포인트 조회",
        operation_description="DB에 저장된 모든 포인트 정보를 조회합니다.",  
        request_body=None,
        responses={200: PointSerializer(many=True)}
    )
    def get(self, request):
        points = Point.objects.all()
        serializer = PointSerializer(points, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="포인트 생성",
        operation_description="""
        DB에 새로운 포인트 정보를 생성합니다.
        price: 포인트의 가격
        point: 포인트의 양
        참고: price는 문자열로 저장됩니다. (ex. "1000원")
        """,
        request_body=PointRequestSerializer,
        responses={400: "fields missing.", 201: PointSerializer}
    )
    def post(self, request):
        price = request.data.get('price')
        point = request.data.get('point')
        if not price or not point:
            return Response({"detail": "fields missing."}, status=status.HTTP_400_BAD_REQUEST)
        point = Point.objects.create(price=price, point=point)
        serializer = PointSerializer(point)
        return Response(serializer.data, status=status.HTTP_201_CREATED)