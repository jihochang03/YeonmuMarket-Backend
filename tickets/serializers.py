from rest_framework.serializers import ModelSerializer
from .models import Ticket, TransferRequest, TransferHistory

class TicketSerializer(ModelSerializer):
    class Meta:
        model = Ticket
        fields = "__all__"
class TransferRequestSerializer(ModelSerializer):
    class Meta:
        model = TransferRequest
        fields = ['id', 'ticket', 'buyer', 'buyer_message', 'created_at', 'completed']

class TransferHistorySerializer(ModelSerializer):
    class Meta:
        model = TransferHistory
        fields = ['id', 'ticket', 'transferee', 'transfer_date', 'conversation']
