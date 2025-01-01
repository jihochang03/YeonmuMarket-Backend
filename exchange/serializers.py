# exchange/serializers.py
from rest_framework import serializers
from .models import Exchange
# TicketSerializer를 ExchangeSerializer 클래스 내에서 임포트
class ExchangeSerializer(serializers.ModelSerializer):
    ticket_1 = serializers.SerializerMethodField()
    ticket_2 = serializers.SerializerMethodField()
    user_info = serializers.SerializerMethodField()
    class Meta:
        model = Exchange
        fields = "__all__"

    def get_ticket_1(self, obj):
        from tickets.serializers import TicketSerializer
        return TicketSerializer(obj.ticket_1, context=self.context).data

    def get_ticket_2(self, obj):
        from tickets.serializers import TicketSerializer
        return TicketSerializer(obj.ticket_2, context=self.context).data
    
    def get_user_info(self, obj):
        # `request.user` 정보를 반환
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user = request.user
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
        return None
