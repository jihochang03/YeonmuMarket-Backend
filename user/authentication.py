from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import jwt
from django.conf import settings
import logging
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

class CookieJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        logger.debug(f"Request Cookies: {request.COOKIES}")
        token = request.COOKIES.get("access_token")
        if not token:
            logger.warning("Access token not found")
            return None

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            logger.debug(f"Decoded JWT Payload: {payload}")
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Invalid token")

        try:
            user = User.objects.get(id=payload["user_id"])
        except User.DoesNotExist:
            raise AuthenticationFailed("User not found")

        logger.debug(f"Authenticated User: {user}")
        return (user, None)
