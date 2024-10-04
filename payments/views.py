from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import AccountSerializer
from user.models import UserProfile
from django.contrib.auth.models import User
import random

# AccountRegisterView: 계좌 등록 및 송금자 이름 생성
class AccountRegisterView(APIView):
    @swagger_auto_schema(
        operation_id="계좌 등록",
        operation_description="계좌 정보를 등록합니다.",
        request_body=AccountSerializer,
        responses={201: openapi.Response(
            description="Account registered successfully",
            examples={
                "application/json": {
                    "detail": "Account registered successfully.",
                    "account": {
                        "id": 1,
                        "bank_account": "1234567890",
                        "bank_name": "KB국민은행"
                    }
                }
            }
        ),
        400: openapi.Response(
            description="Invalid input data",
            examples={
                "application/json": {"account_number": ["This field is required."]}
            }
        )}
    )
    def post(self, request):
        user = request.user
        user_profile = UserProfile.objects.get(user=user)

        serializer = AccountSerializer(data=request.data)
        if serializer.is_valid():
            account = serializer.save(user=user)

            # Update the UserProfile with the bank information
            user_profile.bank_account = account.account_number
            user_profile.bank_name = account.bank_name
            user_profile.is_payment_verified = True
            user_profile.save()

            return Response({
                "detail": "Account registered successfully.",
                "account": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# AccountDetailView: 유저 계좌 정보 조회
class AccountDetailView(APIView):
    @swagger_auto_schema(
        operation_id="계좌 정보 확인",
        operation_description="사용자가 자신의 계좌 정보를 확인합니다.",
        responses={
            200: openapi.Response(
                description="User's bank account information",
                examples={
                    "application/json": {
                        "bank_account": "1234567890",
                        "bank_name": "KB국민은행"
                    }
                }
            ),
            404: openapi.Response(description="Account not found for the user")
        }
    )
    def get(self, request):
        user = request.user
        try:
            user_profile = UserProfile.objects.get(user=user)
            bank_account = user_profile.bank_account
            bank_name = user_profile.bank_name

            if not bank_account:
                return Response({"detail": "No account linked to the user."}, status=status.HTTP_404_NOT_FOUND)

            return Response({
                "bank_account": bank_account,
                "bank_name": bank_name
            }, status=status.HTTP_200_OK)

        except UserProfile.DoesNotExist:
            return Response({"detail": "UserProfile not found."}, status=status.HTTP_404_NOT_FOUND)


# AccountRegisterAndVerifyView: 새 계좌 등록 및 기존 계좌 삭제
class AccountAddView(APIView):
    @swagger_auto_schema(
        operation_id="새 계좌 등록",
        operation_description="새로운 계좌를 추가하고 기존 계좌는 삭제됩니다.",
        request_body=AccountSerializer,
        responses={
            201: openapi.Response(
                description="New account added successfully",
                examples={
                    "application/json": {
                        "detail": "New account registered.",
                        "account": {
                            "id": 2,
                            "bank_account": "9876543210",
                            "bank_name": "우리은행"
                        }
                    }
                }
            ),
            400: openapi.Response(description="Bad request"),
            404: openapi.Response(description="UserProfile not found")
        }
    )
    def post(self, request):
        user = request.user
        try:
            user_profile = UserProfile.objects.get(user=user)

            serializer = AccountSerializer(data=request.data)
            if serializer.is_valid():
                # 기존 계좌 삭제
                old_account = user_profile.bank_account
                if old_account:
                    user_profile.bank_account = None
                    user_profile.bank_name = None
                    user_profile.save()

                # 새 계좌 등록
                new_account = serializer.save(user=user)

                user_profile.bank_account = new_account.account_number
                user_profile.bank_name = new_account.bank_name
                user_profile.save()

                return Response({
                    "detail": "New account registered.",
                    "account": serializer.data
                }, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except UserProfile.DoesNotExist:
            return Response({"detail": "UserProfile not found."}, status=status.HTTP_404_NOT_FOUND)

