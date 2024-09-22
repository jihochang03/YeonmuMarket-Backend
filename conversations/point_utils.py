# conversations/point_utils.py
from user.models import UserProfile
from rest_framework.response import Response
from rest_framework import status

def deduct_points(user_profile: UserProfile, points: int) -> Response:
    if user_profile.remaining_points < points:
        return Response({"detail": "Not enough points."}, status=status.HTTP_400_BAD_REQUEST)
    
    user_profile.remaining_points -= points
    user_profile.save()
    return Response({"detail": "Points deducted successfully."}, status=status.HTTP_200_OK)

def add_points(user_profile: UserProfile, points: int) -> Response:
    user_profile.remaining_points += points
    user_profile.save()
    return Response({"detail": "Points added successfully."}, status=status.HTTP_200_OK)
