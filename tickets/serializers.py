from rest_framework import serializers
from .models import Ticket, TransferRequest, TransferHistory

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['id', 'date', 'seat', 'booking_details', 'price', 'casting', 'owner']

class TransferRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransferRequest
        fields = ['id', 'ticket', 'buyer', 'buyer_message', 'created_at', 'completed']

class TransferHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransferHistory
        fields = ['id', 'ticket', 'transferee', 'transfer_date', 'conversation']
