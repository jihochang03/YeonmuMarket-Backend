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
from django.http import HttpResponseRedirect, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user.models import UserProfile, UserFCMToken
from payments.models import Account
import json

kakao_secret = settings.KAKAO_KEY
kakao_redirect_uri = settings.KAKAO_REDIRECT_URI

def set_token_on_response_cookie(user, status_code) -> Response:
    token = RefreshToken.for_user(user)
    userProfile = UserProfile.objects.get(user=user)
    serialized_data = UserProfileSerializer(userProfile).data
    res = Response(serialized_data, status=status_code)
    res.set_cookie("refresh_token", value=str(token))
    res.set_cookie("access_token", value=str(token.access_token), secure=True, samesite='None')
    return res

class KakaoLoginView(View):
    def get(self, request):
        kakao_auth_url = f"https://kauth.kakao.com/oauth/authorize?client_id={kakao_secret}&redirect_uri={kakao_redirect_uri}&response_type=code"
        return redirect(kakao_auth_url)

class TokenRefreshView(APIView):
    @swagger_auto_schema(
        operation_id="토큰 재발급",
        operation_description="access 토큰을 재발급 받습니다.",
        request_body=TokenRefreshRequestSerializer,
        responses={200: UserSerializer, 400: "Bad Request", 401: "Unauthorized"},
        manual_parameters=[openapi.Parameter("Authorization", openapi.IN_HEADER, description="access token", type=openapi.TYPE_STRING)]
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "no refresh token"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            RefreshToken(refresh_token).verify()
        except:
            return Response(
                {"detail": "please signin again."}, status=status.HTTP_401_UNAUTHORIZED
            )
        new_access_token = str(RefreshToken(refresh_token).access_token)
        response = Response({"detail": "token refreshed"}, status=status.HTTP_200_OK)
        response.set_cookie("access_token", value=str(new_access_token), httponly=True)
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
    
@method_decorator(csrf_exempt, name='dispatch')
class KakaoSignInCallbackView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        # Step 1: Authorization code 확인
        code = request.GET.get("code")
        print(f"Authorization code received: {code}")  # 디버깅: Authorization code 출력
        
        if not code:
            return Response({"error": "Authorization code is missing."}, status=status.HTTP_400_BAD_REQUEST)

        # Step 2: 카카오 토큰 요청 URL 구성 및 요청
        request_uri = f"https://kauth.kakao.com/oauth/token?grant_type=authorization_code&client_id={kakao_secret}&redirect_uri={kakao_redirect_uri}&code={code}"
        print(f"Token request URL: {request_uri}")  # 디버깅: 카카오 토큰 요청 URL 출력
        try:
            response = requests.post(request_uri)
            response_data = response.json()
            print("Kakao token response:", response_data)  # 디버깅: 카카오 응답 출력

            access_token = response_data.get("access_token")
            print(f"Access token received: {access_token}")  # 디버깅: Access token 출력
            if not access_token:
                return Response({"error": "Failed to retrieve access token."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error requesting access token: {str(e)}")  # 디버깅: 에러 메시지 출력
            return Response({"error": "Error requesting access token."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Step 3: 액세스 토큰으로 사용자 정보 가져오기
        try:
            user_info_response = requests.get(
                "https://kapi.kakao.com/v2/user/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_info = user_info_response.json()
            print("Kakao user info response:", user_info)  # 디버깅: 사용자 정보 응답 출력

            if 'id' not in user_info:
                print("Kakao user info missing 'id' field.")  # 디버깅: 사용자 정보 오류 출력
                return Response({"error": "Failed to retrieve user information."}, status=status.HTTP_400_BAD_REQUEST)

            kakao_id = user_info.get("id")
            kakao_email = user_info.get("kakao_account", {}).get("email", "no_email")
            print(f"Kakao ID: {kakao_id}, Email: {kakao_email}")  # 디버깅: 사용자 ID 및 이메일 출력
        except Exception as e:
            print(f"Error fetching user info: {str(e)}")  # 디버깅: 에러 메시지 출력
            return Response({"error": "Error fetching user info."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Step 4: 사용자 조회 또는 생성
        try:
            user = User.objects.get(username=kakao_id)
            print(f"User already exists: {user.username}")  # 디버깅: 사용자 이미 존재
        except User.DoesNotExist:
            print("User does not exist. Creating new user.")  # 디버깅: 사용자 없음
            # 새로운 사용자 생성
            user_data = {
                "username": kakao_id,
                "password": "social_login_password",  # 기본 비밀번호 설정
            }
            user_serializer = UserSerializer(data=user_data)
            print(f"User data for serializer: {user_data}")  # 디버깅: 직렬화 데이터 출력
            if user_serializer.is_valid():
                user_serializer.validated_data["password"] = make_password(user_serializer.validated_data["password"])
                user = user_serializer.save()
                print(f"New user created: {user.username}")  # 디버깅: 새 사용자 생성 로그
            else:
                print("User serializer errors:", user_serializer.errors)  # 디버깅: 직렬화 에러 출력
                return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # 사용자 프로필 생성
            try:
                UserProfile.objects.create(user=user, is_social_login=True, kakao_email=kakao_email)
                print(f"User profile created for user: {user.username}")  # 디버깅: 프로필 생성 로그
            except Exception as e:
                print(f"Error creating user profile: {str(e)}")  # 디버깅: 프로필 생성 에러 출력
                return Response({"error": "Error creating user profile."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Step 5: JWT 토큰 설정 및 응답
        try:
            response = set_token_on_response_cookie(user, status_code=status.HTTP_200_OK)
            print(f"JWT token set for user: {user.username}")  # 디버깅: 토큰 설정 성공 로그
            return response
        except Exception as e:
            print(f"Error setting JWT token: {str(e)}")  # 디버깅: 토큰 설정 에러 출력
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


class SaveFcmTokenView(APIView):
    def post(self, request: HttpRequest):
        data = json.loads(request.body)
        print(data)
        token = data.get('token')
        user = request.user  # 인증된 사용자로 토큰 저장
        
        if token:
            UserFCMToken.objects.get_or_create(user=user, fcm_token=token)
            return Response({"message": "success"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Token is missing"}, status=status.HTTP_401_UNAUTHORIZED)
    