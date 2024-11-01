from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import AccountSerializer
from django.http import HttpRequest
from .models import Account
import json

# AccountRegisterView: 계좌 등록 및 송금자 이름 생성
class AccountRegisterView(APIView):
    @swagger_auto_schema(
        operation_id="계좌 등록",
        operation_description="계좌 정보를 등록합니다.",
        request_body=AccountSerializer,
        security=[{"Bearer": []}],
        responses={201: openapi.Response(
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
        )}
    )
    def post(self, request: HttpRequest):
        user = request.user
        print(user)
        if not user.is_authenticated:
            return Response({"detail": "please signin"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            account = Account.objects.get(user=user)
            return Response({"detail": "Account Already exists."}, status=status.HTTP_400_BAD_REQUEST)
        except Account.DoesNotExist:
            data = json.loads(request.body)
            bank_account = data["accountNum"]
            bank_name = data["bank"]

            data={'bank_account': bank_account, 'bank_name': bank_name}
            serializer = AccountSerializer(data=data)

            if serializer.is_valid():
                serializer.save(user=user)
                # TODO: 계좌 유효성 여부 검사 로직 넣기
                

                return Response({
                    "detail": "Account registered successfully.",
                    "account": serializer.data
                }, status=status.HTTP_201_CREATED)

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
        if not user.is_authenticated:
            return Response({"detail": "please signin"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            account = Account.objects.get(user=user)

            data=json.loads(request.body)

            data={'bank_account': data["bank_account"], 'bank_name': data["bank_name"]}

            serializer = AccountSerializer(data=data)

            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            account.bank_account = data["bank_account"]
            account.bank_name = data["bank_name"]
            account.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Account.DoesNotExist:
            return Response({"error": "account does not exist"}, status=status.HTTP_404_NOT_FOUND)
        
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

        