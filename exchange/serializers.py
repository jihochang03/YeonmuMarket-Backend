# exchange/serializers.py
from rest_framework import serializers
from .models import Exchange
# TicketSerializer를 ExchangeSerializer 클래스 내에서 임포트
class ExchangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exchange
        fields = "__all__"

    def get_ticket_1(self, obj):
        from tickets.serializers import TicketSerializer
        return TicketSerializer(obj.ticket_1).data  # TicketSerializer를 내부에서 임포트하여 사용
    
    def get_ticket_2(self, obj):
        from tickets.serializers import TicketSerializer
        return TicketSerializer(obj.ticket_2).data  # TicketSerializer를 내부에서 임포트하여 사용
