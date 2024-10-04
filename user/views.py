from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import status
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

kakao_secret = settings.KAKAO_KEY
kakao_redirect_uri = settings.KAKAO_REDIRECT_URI

def set_token_on_response_cookie(user, status_code) -> Response:
    token = RefreshToken.for_user(user)
    user_profile = UserProfile.objects.get(user=user)
    serialized_data = UserProfileSerializer(user_profile).data
    res = Response(serialized_data, status=status_code)
    res.set_cookie("refresh_token", value=str(token))
    res.set_cookie("access_token", value=str(token.access_token))
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

class KakaoSignInCallbackView(APIView):
    @swagger_auto_schema(
        operation_description="Kakao social login callback API. Takes a code from the frontend and exchanges it for an access token.",
        manual_parameters=[
            openapi.Parameter(
                'code', openapi.IN_QUERY, description="Authorization code from Kakao", type=openapi.TYPE_STRING
            )
        ],
        responses={
            200: openapi.Response(
                description="Kakao login successful",
                examples={
                    "application/json": {
                        "message": "Login successful",
                        "redirect_url": "/home/"
                    }
                }
            ),
            400: openapi.Response(description="Invalid code or failed request"),
        }
    )
    def post(self, request):
        # 프론트에서 전달된 code로 카카오에서 access_token 요청
        code = request.GET.get("code")  # 나중에 request.body로 변경 가능

        # 카카오로부터 access_token을 요청
        token_url = (
            f"https://kauth.kakao.com/oauth/token?"
            f"grant_type=authorization_code&client_id={kakao_secret}&"
            f"redirect_uri={kakao_redirect_uri}&code={code}"
        )
        token_response = requests.post(token_url)
        access_token = token_response.json().get("access_token")

        # access_token으로 카카오 유저 정보를 요청
        user_info_response = requests.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_info = user_info_response.json()

        kakao_id = user_info.get("id")
        kakao_email = user_info.get("kakao_account").get("email")

        try:
            # 유저가 존재하는지 확인
            user = User.objects.get(username=kakao_id)
        except User.DoesNotExist:
            # 유저가 존재하지 않으면 생성
            user_data = {
                "username": kakao_id,
                "password": "social_login_password",
            }
            user_serializer = UserSerializer(data=user_data)
            if user_serializer.is_valid(raise_exception=True):
                # 비밀번호를 해시화한 후 저장
                user_serializer.validated_data["password"] = make_password(
                    user_serializer.validated_data["password"]
                )
                user = user_serializer.save()

            # 새로 생성된 유저 프로필 저장
            UserProfile.objects.create(
                user=user,
                #is_social_login=True,
                kakao_email=kakao_email,
                kakao_token=access_token,  # access_token 저장
            )

            user_profile = UserProfile.objects.get(user=user)

            # 계좌 등록 여부에 따라 리다이렉트
            if user_profile.is_payment_verified:
            # 계좌가 등록된 경우 홈으로 리다이렉트
                return redirect('home')
            else:
            # 계좌가 등록되지 않은 경우 계좌 등록 페이지로 리다이렉트
                return redirect('account-register')

        # 로그인이 완료되면 토큰을 설정하여 응답에 포함 (JWT나 세션 기반)
        return set_token_on_response_cookie(user, status_code=status.HTTP_200_OK)