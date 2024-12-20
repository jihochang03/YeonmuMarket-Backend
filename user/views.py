from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import UserProfile
from django.conf import settings
from django.shortcuts import redirect
from django.views import View
import requests
from .serializers import UserSerializer, UserProfileSerializer
from .request_serializers import TokenRefreshRequestSerializer, SignOutRequestSerializer, UserProfileUpdateRequestSerializer
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user.models import UserProfile
from payments.models import Account
from django.middleware.csrf import get_token

kakao_secret = settings.KAKAO_KEY
kakao_redirect_uri = 'https://www.yeonmu.shop/auth'

def set_token_on_response_cookie(user, status_code) -> Response:
    token = RefreshToken.for_user(user)
    userProfile = UserProfile.objects.get(user=user)
    serialized_data = UserProfileSerializer(userProfile).data
    res = Response(serialized_data, status=status_code)
    res.set_cookie(
        "refresh_token",
        value=str(token),
        httponly=True,  # Only accessible via HTTP, improves security
        secure=True,  # Ensures cookies are sent over HTTPS only
        samesite="None",  # Required for cross-origin requests
        domain=".yeonmu.shop",
    )
    res.set_cookie(
        "access_token",
        value=str(token.access_token),
        httponly=True,  # Same as above
        secure=True,
        samesite="None",
        domain=".yeonmu.shop",
    )
    return res

import logging

logger = logging.getLogger("django")

class KakaoLoginView(View):
    def get(self, request):
        kakao_auth_url = f"https://kauth.kakao.com/oauth/authorize?client_id={kakao_secret}&redirect_uri=https://www.yeonmu.shop/auth&response_type=code"
        logger.info(f"Kakao redirect URI: {kakao_redirect_uri}")
        return redirect(kakao_auth_url)

@method_decorator(csrf_exempt, name='dispatch')
class TokenCSRFView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        csrf_token = get_token(request)
        response = Response({"detail": "token CSRF"}, status=status.HTTP_200_OK)
        response.set_cookie(
            key='csrftoken',
            value=csrf_token,
            domain='.yeonmu.shop',
            secure=True,
            httponly=False, # 반드시 False
            samesite='None'
        )
        return response
class TokenRefreshView(APIView):
    @swagger_auto_schema(
        operation_id="토큰 재발급",
        operation_description="access 토큰을 재발급 받습니다.",
        request_body=TokenRefreshRequestSerializer,
        responses={200: UserSerializer, 400: "Bad Request", 401: "Unauthorized"},
        manual_parameters=[
            openapi.Parameter(
                "Authorization", openapi.IN_HEADER,
                description="access token",
                type=openapi.TYPE_STRING
            )
        ]
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "no refresh token provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Refresh Token 검증
            token = RefreshToken(refresh_token)
            token.verify()
        except Exception as e:
            return Response(
                {"detail": "Invalid or expired refresh token", "error": str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # 새로운 Access Token 생성
        new_access_token = str(token.access_token)

        # Access Token을 쿠키로 설정
        response = Response(
            {"detail": "Access token refreshed successfully"},
            status=status.HTTP_200_OK
        )
        response.set_cookie(
            "access_token",
            value=new_access_token,
            httponly=True,
            secure=True,  # HTTPS를 사용하는 경우에만 활성화
            max_age=15 * 60,  # Access Token 만료 시간 (15분)
        )
        return response


class SignOutView(APIView):
    @swagger_auto_schema(
        operation_id="로그아웃",
        operation_description="로그아웃을 진행합니다.",
        request_body=SignOutRequestSerializer,
        responses={204: "No Content", 400: "Bad Request", 401: "Unauthorized"},
        manual_parameters=[openapi.Parameter("Authorization", openapi.IN_HEADER, description="access token", type=openapi.TYPE_STRING)]
    )
    def post(self, request):

        if not request.user.is_authenticated:
            return Response(
                {"detail": "please signin"}, status=status.HTTP_401_UNAUTHORIZED
            )

        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "no refresh token"}, status=status.HTTP_400_BAD_REQUEST
            )
        RefreshToken(refresh_token).blacklist()

        return Response(status=status.HTTP_204_NO_CONTENT)
class UserProfileListView(APIView):
    @swagger_auto_schema(
        operation_id="유저 정보 확인",
        operation_description="등록된 모든 유저 정보를 가져옵니다",
        request_body=None,
        responses={200: UserProfileSerializer(many=True), 401: "please signin"},
        manual_parameters=[openapi.Parameter("Authorization", openapi.IN_HEADER, description="access token", type=openapi.TYPE_STRING)]
    )
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "please signin"}, status=status.HTTP_401_UNAUTHORIZED)
        user_profile = UserProfile.objects.all()
        serializer = UserProfileSerializer(user_profile, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class UserProfileDetailView(APIView):
    @swagger_auto_schema(
        operation_id="유저 정보 확인",
        operation_description="토큰을 기반으로, 유저 세부 정보를 가져옵니다.",
        request_body=None,
        responses={200: UserProfileSerializer, 404: "UserProfile Not found.", 401: "please signin"},
        manual_parameters=[openapi.Parameter("Authorization", openapi.IN_HEADER, description="access token", type=openapi.TYPE_STRING)]
    )
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "please signin"}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            user_profile = UserProfile.objects.get(user=user)
            serializer = UserProfileSerializer(user_profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            return Response({"detail": "UserProfile Not found."}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_id="유저 정보 수정",
        operation_description="유저 개인 프로필 정보(닉네임, 프로필 사진)를 수정합니다.",
        request_body=UserProfileUpdateRequestSerializer,
        responses={200: UserProfileSerializer, 400: "[profilepic_id, nickname] fields missing.", 401: "please signin", 404: "UserProfile Not found."},
        manual_parameters=[openapi.Parameter("Authorization", openapi.IN_HEADER, description="access token", type=openapi.TYPE_STRING)]
    )
    def put(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "please signin"}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            user_profile = UserProfile.objects.get(user=user)
            profilepic_id = request.data.get("profilepic_id")
            nickname = request.data.get("nickname")
            if not profilepic_id or not nickname:
                return Response({"detail": "[profilepic_id, nickname] fields missing."}, status=status.HTTP_400_BAD_REQUEST)
            user_profile.profilepic_id=profilepic_id
            user_profile.nickname = nickname
            user_profile.save()
            serializer = UserProfileSerializer(user_profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            return Response({"detail": "UserProfile Not found."}, status=status.HTTP_404_NOT_FOUND)
        
class CheckUsernameView(APIView):
    @swagger_auto_schema(
        operation_id="유저명 중복 확인",
        operation_description="유저명이 이미 존재하는지 확인합니다.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "username": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="중복을 확인할 유저명",
                )
            },
        ),
        responses={200: "Username is available", 400: "Username already exists"},
    )
    def post(self, request):
        username = request.data.get("username")
        if User.objects.filter(username=username).exists():
            return Response({"message": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Username is available"}, status=status.HTTP_200_OK)
    
import logging

logger = logging.getLogger("django")

@method_decorator(csrf_exempt, name='dispatch')
class KakaoSignInCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Step 1: Authorization code 확인
        code = request.GET.get("code")
        logger.info(f"Authorization code received: {code}")

        if not code:
            logger.error("Authorization code is missing.")
            return Response({"error": "Authorization code is missing."}, status=status.HTTP_400_BAD_REQUEST)

        # Step 2: 카카오 토큰 요청 URL 구성 및 요청
        request_uri = f"https://kauth.kakao.com/oauth/token?grant_type=authorization_code&client_id={kakao_secret}&redirect_uri={kakao_redirect_uri}&code={code}"
        logger.debug(f"Token request URL: {request_uri}")

        try:
            response = requests.post(request_uri)
            response_data = response.json()
            logger.info(f"Kakao token response: {response_data}")

            access_token = response_data.get("access_token")
            logger.info(f"Access token received: {access_token}")
            if not access_token:
                logger.error("Failed to retrieve access token.")
                return Response({"error": "Failed to retrieve access token."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"Error requesting access token: {str(e)}")
            return Response({"error": "Error requesting access token."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Step 3: 액세스 토큰으로 사용자 정보 가져오기
        try:
            user_info_response = requests.get(
                "https://kapi.kakao.com/v2/user/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_info = user_info_response.json()
            logger.info(f"Kakao user info response: {user_info}")

            if 'id' not in user_info:
                logger.error("Kakao user info missing 'id' field.")
                return Response({"error": "Failed to retrieve user information."}, status=status.HTTP_400_BAD_REQUEST)

            kakao_id = user_info.get("id")
            kakao_email = user_info.get("kakao_account", {}).get("email", "no_email")
            logger.info(f"Kakao ID: {kakao_id}, Email: {kakao_email}")
        except Exception as e:
            logger.exception(f"Error fetching user info: {str(e)}")
            return Response({"error": "Error fetching user info."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Step 4: 사용자 조회 또는 생성
        try:
            user = User.objects.get(username=kakao_id)
            logger.info(f"User already exists: {user.username}")
        except User.DoesNotExist:
            logger.info("User does not exist. Creating new user.")
            # 새로운 사용자 생성
            user_data = {
                "username": kakao_id,
                "password": "social_login_password",  # 기본 비밀번호 설정
            }
            user_serializer = UserSerializer(data=user_data)
            logger.debug(f"User data for serializer: {user_data}")
            if user_serializer.is_valid():
                user_serializer.validated_data["password"] = make_password(user_serializer.validated_data["password"])
                user = user_serializer.save()
                logger.info(f"New user created: {user.username}")
            else:
                logger.error(f"User serializer errors: {user_serializer.errors}")
                return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # 사용자 프로필 생성
            try:
                UserProfile.objects.create(user=user, is_social_login=True, kakao_email=kakao_email)
                logger.info(f"User profile created for user: {user.username}")
            except Exception as e:
                logger.exception(f"Error creating user profile: {str(e)}")
                return Response({"error": "Error creating user profile."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Step 5: JWT 토큰 설정 및 응답
        try:
            response = set_token_on_response_cookie(user, status_code=status.HTTP_200_OK)
            logger.info(f"response : {response}")
            logger.info(f"JWT token set for user: {user.username}")
            return response
        except Exception as e:
            logger.exception(f"Error setting JWT token: {str(e)}")
            return Response({"error": "Error setting JWT token."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class UserAccountDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id="계정 탈퇴",
        operation_description="사용자의 계정을 삭제합니다.",
        responses={
            204: openapi.Response(
                description="User account deleted successfully",
                examples={
                    "application/json": {
                        "detail": "User account deleted successfully."
                    }
                }
            ),
            401: openapi.Response(description="Unauthorized user"),
        }
    )
    @transaction.atomic
    def delete(self, request):
        user = request.user

        # 관련된 UserProfile 삭제
        try:
            user_profile = UserProfile.objects.get(user=user)
            user_profile.delete()
        except UserProfile.DoesNotExist:
            pass

        # 관련된 Account 삭제
        try:
            account = Account.objects.get(user=user)
            account.delete()
        except Account.DoesNotExist:
            pass

        # 사용자 계정 삭제
        user.delete()

        return Response({"detail": "User account deleted successfully."}, status=status.HTTP_204_NO_CONTENT) 
