from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import jwt
from django.conf import settings
import logging
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from rest_framework.response import Response


logger = logging.getLogger(__name__)

class CookieJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        logger.debug(f"Request Cookies: {request.COOKIES}")
        token = request.COOKIES.get("access_token")
        payload = None  # payload 초기화

        if not token:
            logger.warning("Access token not found")
            return None

        try:
            # Decode access token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            logger.debug(f"Decoded JWT Payload: {payload}")
        except jwt.ExpiredSignatureError:
            logger.warning("Access token expired, attempting to refresh...")

            # Access Token 만료 시 Refresh Token 확인
            refresh_token = request.COOKIES.get("refresh_token")
            if not refresh_token:
                raise AuthenticationFailed("Refresh token not found")

            try:
                # Refresh Token 검증
                refresh_payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=["HS256"])
                logger.debug(f"Decoded Refresh Token Payload: {refresh_payload}")

                # 새로운 Access Token 생성
                new_access_token = jwt.encode({
                    "user_id": refresh_payload["user_id"],
                    "exp": datetime.utcnow() + timedelta(minutes=15),
                    "iat": datetime.utcnow()
                }, settings.SECRET_KEY, algorithm="HS256")
                logger.info("New access token generated")
                request.META['new_access_token'] = new_access_token

                payload = refresh_payload  # Refresh Payload로 대체
            except jwt.ExpiredSignatureError:
                raise AuthenticationFailed("Refresh token has expired")
            except jwt.InvalidTokenError:
                raise AuthenticationFailed("Invalid refresh token")

        except jwt.InvalidTokenError:
            logger.warning("Invalid access token")
            raise AuthenticationFailed("Invalid token")

        # payload가 None인 경우 확인
        if not payload:
            raise AuthenticationFailed("Authentication failed: No valid payload")

        try:
            user = User.objects.get(id=payload["user_id"])
        except User.DoesNotExist:
            raise AuthenticationFailed("User not found")

        logger.debug(f"Authenticated User: {user}")
        
        # 사용자와 새 토큰 반환
        return (user, request.META.get('new_access_token', None))