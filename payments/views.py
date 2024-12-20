from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import AccountSerializer
from django.http import HttpRequest
from .models import Account
import json
import logging
from user.models import UserProfile

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,  # 디버깅 로그를 출력
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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

    # 로깅 설정
    

    def post(self, request: HttpRequest):
        user = request.user
        logger.info("Post request received")
        logger.debug(f"Authenticated User: {user}")

        if not user.is_authenticated:
            logger.warning("User not authenticated")
            return Response({"detail": "Please sign in"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            # Check if the account already exists
            logger.info(f"Checking if account exists for user: {user}")
            user_profile = UserProfile.objects.get(user=user)
            user_profile.is_payment_verified = True
            user_profile.save()
            logger.info("Account already exists and is_payment_verified updated")
            return Response({"detail": "Account Already exists."}, status=status.HTTP_201_CREATED)
        except Account.DoesNotExist:
            logger.info("Account does not exist for user, creating a new account")

            # Parse the request body
            try:
                data = json.loads(request.body)
                logger.debug(f"Request Data: {data}")
            except json.JSONDecodeError as e:
                logger.error("Failed to decode request body", exc_info=True)
                return Response({"detail": "Invalid request body"}, status=status.HTTP_400_BAD_REQUEST)

            # Extract data from the request
            bank_account = data.get("accountNum")
            bank_name = data.get("bank")
            account_holder = data.get("account_holder")
            logger.debug(f"Bank Account: {bank_account}, Bank Name: {bank_name}, Account Holder: {account_holder}")

            # Prepare serializer data
            serializer_data = {
                "bank_account": bank_account,
                "bank_name": bank_name,
                "account_holder": account_holder,
                "is_payment_verified": True,
            }

            # Validate and save account data
            serializer = AccountSerializer(data=serializer_data)
            if serializer.is_valid():
                logger.info("Serializer is valid, saving the account")
                account = serializer.save(user=user)

                # Update user profile
                user_profile = UserProfile.objects.get(user=user)
                user_profile.is_payment_verified = True
                user_profile.save()
                logger.info("Account registered successfully and user profile updated")

                return Response({
                    "detail": "Account registered successfully.",
                    "account": AccountSerializer(account).data
                }, status=status.HTTP_201_CREATED)
            else:
                logger.error("Serializer validation failed", extra={"errors": serializer.errors})
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
    def put(self, request):
        user = request.user
        print(request.data)
        try:
            data = request.data
            bank_account = data.get("accountNum")
            bank_name = data.get("bank")
            account_holder = data.get("account_holder")

            # Check for required fields
            if not bank_account or not bank_name or not account_holder:
                return Response({"detail": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)
            serializer_data = {
                "bank_account": bank_account,
                "bank_name": bank_name,
                "account_holder": account_holder,
                "is_payment_verified": True,  # Add this field
            }
            # Serialize and save the data
            serializer = AccountSerializer(data=serializer_data)
            if serializer.is_valid():
                account = serializer.save(user=user)  # Pass the user to the save method
                return Response({
                    "detail": "Account modified successfully.",
                    "account": AccountSerializer(account).data
                }, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print("Error updating account:", e)
            return Response({"detail": "An error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            "bank_name": account_info.bank_name,
            "account_holder": account_info.account_holder
            }, status=status.HTTP_200_OK)
        except Account.DoesNotExist:
            return Response({"detail": "No account linked to the user."}, status=status.HTTP_404_NOT_FOUND)
