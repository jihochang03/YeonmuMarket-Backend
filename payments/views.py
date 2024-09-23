from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Account, AccountVerification
from .serializers import AccountSerializer
from user.models import UserProfile
from django.contrib.auth.models import User
import random


# 공통 기능을 함수로 분리

def send_small_amount(account_number, bank_name, amount):
    #추가 필요"
    print(f"송금 {amount}원을 {bank_name} - {account_number}로 송금했습니다.")

def generate_random_name():
    #"""송금자 이름을 랜덤으로 생성."""
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=4))

def verify_and_update_account(user, account, verification_code_input):
    #"""계좌 검증 후 유효한 경우 계좌 업데이트 및 기존 계좌 삭제 처리."""
    try:
        verification = AccountVerification.objects.get(account=account)
        if verification.verification_code == verification_code_input:
            verification.is_verified = True
            verification.save()

            account.is_verified = True
            account.save()

            # 기존 계좌 삭제 및 새 계좌 등록
            user_profile = UserProfile.objects.get(user=user)
            old_account = user_profile.bank_account
            if old_account and old_account != account:
                old_account.delete()

            user_profile.bank_account = account
            user_profile.save()

            return {"detail": "New account verified and old account deleted successfully."}, status.HTTP_200_OK
        else:
            return {"detail": "Verification failed. Incorrect code."}, status.HTTP_400_BAD_REQUEST
    except AccountVerification.DoesNotExist:
        return {"detail": "Verification not found."}, status.HTTP_404_NOT_FOUND


# AccountRegisterView: 계좌 등록 및 송금자 이름 생성
class AccountRegisterView(APIView):
    @swagger_auto_schema(
        operation_id="계좌 등록",
        operation_description="계좌 정보를 등록하고, 1원을 송금합니다. 이후 송금자의 이름 첫 4글자를 입력해 인증을 진행해야 합니다.",
        request_body=AccountSerializer,
        responses={201: "Account registered successfully.", 400: "Invalid data"}
    )
    def post(self, request):
        user = request.user
        user_profile = UserProfile.objects.get(user=user)

        serializer = AccountSerializer(data=request.data)
        if serializer.is_valid():
            account = serializer.save(user=user)

            # 송금 및 검증 코드 생성
            sender_name = generate_random_name()
            send_small_amount(account.account_number, account.bank_name, amount=1)
            verification_code = sender_name[:4]

            AccountVerification.objects.create(account=account, verification_code=verification_code)

            return Response({
                "detail": "Account registered. Please verify by entering the first 4 letters of the sender's name.",
                "account": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# AccountVerifyView: 계좌 인증
class AccountVerifyView(APIView):
    @swagger_auto_schema(
        operation_id="계좌 인증",
        operation_description="송금자의 이름 첫 4글자를 입력해 계좌를 인증합니다.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'verification_code': openapi.Schema(type=openapi.TYPE_STRING, description="송금자의 이름 첫 4글자"),
            },
        ),
        responses={200: "Account verified successfully.", 400: "Verification failed. Incorrect code.", 404: "Verification not found."}
    )
    def post(self, request, account_id):
        user = request.user
        account = Account.objects.get(id=account_id, user=user)

        entered_verification_code = request.data.get("verification_code")
        response_data, response_status = verify_and_update_account(user, account, entered_verification_code)

        return Response(response_data, status=response_status)


# AccountDetailView: 유저 계좌 정보 조회
class AccountDetailView(APIView):
    
    @swagger_auto_schema(
        operation_id="계좌 정보 확인",
        operation_description="사용자가 자신의 계좌 정보를 확인합니다.",
        responses={200: AccountSerializer, 404: "Account not found for the user"}
    )
    def get(self, request):
        user = request.user
        try:
            user_profile = UserProfile.objects.get(user=user)
            account = user_profile.bank_account
            if not account:
                return Response({"detail": "No account linked to the user."}, status=status.HTTP_404_NOT_FOUND)

            serializer = AccountSerializer(account)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except UserProfile.DoesNotExist:
            return Response({"detail": "UserProfile not found."}, status=status.HTTP_404_NOT_FOUND)


# AccountRegisterAndVerifyView: 새 계좌 등록 및 기존 계좌 삭제
class AccountRegisterAndVerifyView(APIView):
    
    @swagger_auto_schema(
        operation_id="새 계좌 등록 및 검증",
        operation_description="새로운 계좌를 추가하고 검증합니다. 검증 완료 후 기존 계좌는 삭제됩니다.",
        request_body=AccountSerializer,
        responses={200: "New account added and verified, old account deleted successfully.", 400: "Bad request", 404: "UserProfile or Account not found"}
    )
    def post(self, request):
        user = request.user
        try:
            user_profile = UserProfile.objects.get(user=user)

            # 새로운 계좌 직렬화 및 유효성 검사
            serializer = AccountSerializer(data=request.data)
            if serializer.is_valid():
                new_account = serializer.save(user=user)

                # 송금 및 검증 코드 생성
                sender_name = generate_random_name()
                send_small_amount(new_account.account_number, new_account.bank_name, amount=1)
                verification_code = sender_name[:4]

                AccountVerification.objects.create(account=new_account, verification_code=verification_code)

                return Response({
                    "detail": "New account registered. Please verify by entering the first 4 letters of the sender's name.",
                    "account": serializer.data
                }, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except UserProfile.DoesNotExist:
            return Response({"detail": "UserProfile not found."}, status=status.HTTP_404_NOT_FOUND)


# AccountVerifyAndDeleteOldView: 새 계좌 인증 및 기존 계좌 삭제
class AccountVerifyAndDeleteOldView(APIView):
    @swagger_auto_schema(
        operation_id="새 계좌 인증 및 기존 계좌 삭제",
        operation_description="새로운 계좌를 인증하고, 기존 계좌를 삭제합니다.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'verification_code': openapi.Schema(type=openapi.TYPE_STRING, description="송금자의 이름 첫 4글자"),
            },
        ),
        responses={200: "New account verified and old account deleted successfully.", 400: "Verification failed.", 404: "Verification not found."}
    )
    def post(self, request, account_id):
        user = request.user
        account = Account.objects.get(id=account_id, user=user)

        verification_code_input = request.data.get('verification_code')
        response_data, response_status = verify_and_update_account(user, account, verification_code_input)

        return Response(response_data, status=response_status)
