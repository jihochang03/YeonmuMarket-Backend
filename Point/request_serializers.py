from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

class PointRequestSerializer(serializers.Serializer):
  price = serializers.CharField()
  point = serializers.IntegerField()