from rest_framework.serializers import ModelSerializer
from .models import Ticket, TicketPost

class TicketSerializer(ModelSerializer):
    class Meta:
        model = Ticket
        fields = "__all__"

class TicketPostSerializer(ModelSerializer):
    class Meta:
        model = TicketPost
        fields = "__all__"