from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import jwt
from django.conf import settings

class CookieJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # 쿠키에서 access_token 가져오기
        token = request.COOKIES.get("access_token")
        if not token:
            return None  # 쿠키에 토큰이 없으면 인증 실패

        try:
            # JWT 디코딩 및 검증
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token has expired")  # 만료된 토큰
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Invalid token")  # 잘못된 토큰

        # payload에는 사용자 정보가 포함되어 있을 가능성이 있음
        return (payload, None)  # 인증된 사용자 정보와 None 반환
