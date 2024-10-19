from rest_framework import serializers
from .models import Ticket, TicketPost

class TicketSerializer(serializers.ModelSerializer):
    reservation_image_url = serializers.SerializerMethodField()
    seat_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = "__all__"

    def get_reservation_image_url(self, obj):
        # Handle missing request context gracefully
        request = self.context.get('request')
        if request and obj.uploaded_file:
            return request.build_absolute_uri(obj.uploaded_file)
        return None

    def get_seat_image_url(self, obj):
        # Handle missing request context gracefully
        request = self.context.get('request')
        if request and obj.uploaded_seat_image:
            return request.build_absolute_uri(obj.uploaded_seat_image)
        return None

class TicketPostSerializer(serializers.ModelSerializer):
    ticket = TicketSerializer()  # Nest the TicketSerializer to include all ticket details

    class Meta:
        model = TicketPost
        fields = "__all__"
