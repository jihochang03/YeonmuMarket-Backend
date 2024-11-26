from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import AccountSerializer
from django.http import HttpRequest
from .models import Account
import json
from user.models import UserProfile
from .crawling import check_account  # crawling.py의 함수 임포트
class AccountRegisterView(APIView):
    @swagger_auto_schema(
        operation_id="계좌 등록",
        operation_description="계좌 정보를 등록합니다.",
        request_body=AccountSerializer,
        security=[{"Bearer": []}],
        responses={
            201: openapi.Response(
                description="Account registered successfully",
                examples={
                    "application/json": {
                        "detail": "Account registered successfully.",
                        "account": {
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
            ),
            404: openapi.Response(
                description="Account not found",
                examples={
                    "application/json": {"detail": "The account number does not exist in the system."}
                }
            )
        }
    )
    def post(self, request: HttpRequest):
        user = request.user
        print("Authenticated User:", user)

        if not user.is_authenticated:
            print("User not authenticated")
            return Response({"detail": "Please sign in"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            account = Account.objects.get(user=user)
            print("Account already exists for user:", user)
            user_profile = UserProfile.objects.get(user=user)
            user_profile.is_payment_verified = True
            user_profile.save()
            return Response({"detail": "Account Already exists."}, status=status.HTTP_201_CREATED)
        except Account.DoesNotExist:
            data = json.loads(request.body)
            print("Request Data:", data)

            bank_account = data.get("accountNum")
            bank_name = data.get("bank")
            account_holder =data.get("account_holder")
            print("Bank Account:", bank_account)
            print("Bank Name:", bank_name)
            print("account_holder:", account_holder)

            # 계좌 유효성 검사
            #is_valid_account = check_account(bank_account)
            #if not is_valid_account:
                #print("Account validation failed")
                #return Response({"detail": "사기 계좌로 등록되었습니다"},
                                #status=status.HTTP_404_NOT_FOUND)

            # Serializer 초기화 및 검증
            data = {'bank_account': bank_account, 'bank_name': bank_name, 'account_holder': account_holder}
            serializer = AccountSerializer(data=data)
            print("Serializer Data:", serializer.initial_data)

            if serializer.is_valid():
                print("Serializer is valid")
                serializer.save(user=user)

                # 유저 프로필 업데이트
                user_profile = UserProfile.objects.get(user=user)
                user_profile.is_payment_verified = True
                user_profile.save()

                return Response({
                    "detail": "Account registered successfully.",
                    "account": serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                print("Serializer errors:", serializer.errors)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    @swagger_auto_schema(
        operation_id="계좌 정보 수정",
        operation_description="계좌 정보를 수정합니다.",
        request_body=AccountSerializer,
        responses={201: openapi.Response(
            description="Account modified successfully",
            examples={
                "application/json": {
                    "detail": "Account modified successfully.",
                    "account": {

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
    def put(self, request: HttpRequest):
        user = request.user
        try:
            account = Account.objects.get(user=user)
            data = request.data

            bank_account = data.get("accountNum")
            bank_name = data.get("bank")
            account_holder = data.get("account_holder")

            if not bank_account or not bank_name or not account_holder:
                return Response({"detail": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

            # 계좌 유효성 검사 등 필요한 로직 추가 가능

            account.bank_account = bank_account
            account.bank_name = bank_name
            account.account_holder = account_holder
            account.save()

            serializer = AccountSerializer(account)
            return Response({
                "detail": "Account modified successfully.",
                "account": serializer.data
            }, status=status.HTTP_200_OK)

        except Account.DoesNotExist:
            return Response({"detail": "Account does not exist."}, status=status.HTTP_404_NOT_FOUND)
        
    @swagger_auto_schema(
        operation_id="계좌 정보 삭제",
        operation_description="계좌 정보를 삭제합니다.",
        responses={201: openapi.Response(
            description="Account modified successfully",
            examples={
                "application/json": {
                    "detail": "Account modified successfully.",
                    "account": {

                        "bank_account": "1234567890",
                        "bank_name": "KB국민은행"
                    }
                }
            }
        ),
        401: openapi.Response(
            description="Unauthorized user"
        ),
        404: openapi.Response(
            description="account not found"
        )})
    def delete(self, request: HttpRequest):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "please signin"}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            account = Account.objects.get(user=user)
            account.delete()
            return Response({"detail": "account delete success"}, status=status.HTTP_204_NO_CONTENT)

        except Account.DoesNotExist:
            return Response({"detail": "account not found"}, status=status.HTTP_404_NOT_FOUND)

        
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
    def get(self, request: HttpRequest):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "please signin"}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            account_info = Account.objects.get(user=user)
            return Response({
            "bank_account": account_info.bank_account,
            "bank_name": account_info.bank_name
             }, status=status.HTTP_200_OK)
        except Account.DoesNotExist:
            return Response({"detail": "No account linked to the user."}, status=status.HTTP_404_NOT_FOUND)
