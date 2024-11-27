from rest_framework import serializers
from .models import Ticket, TicketPost

class TicketSerializer(serializers.ModelSerializer):
    uploaded_file_url = serializers.SerializerMethodField()
    uploaded_seat_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = "__all__"

    def get_uploaded_file_url(self, obj):
        request = self.context.get('request')
        if obj.masked_file and hasattr(obj.masked_file, 'url'):
            return request.build_absolute_uri(obj.masked_file.url)
        else:
            return None

    def get_uploaded_seat_image_url(self, obj):
        request = self.context.get('request')
        if obj.processed_seat_image and hasattr(obj.processed_seat_image, 'url'):
            return request.build_absolute_uri(obj.processed_seat_image.url)
        else:
            return None

class TicketPostSerializer(serializers.ModelSerializer):
    ticket = TicketSerializer()  # Nest the TicketSerializer to include all ticket details

    class Meta:
        model = TicketPost
        fields = "__all__"
