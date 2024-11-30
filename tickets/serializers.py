from rest_framework import serializers
from .models import Ticket, TicketPost

class TicketSerializer(serializers.ModelSerializer):
    uploaded_masked_file_url = serializers.SerializerMethodField()
    uploaded_file_url=serializers.SerializerMethodField()
    uploaded_processed_seat_image_url = serializers.SerializerMethodField()
    uploaded_seat_image_url= serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = "__all__"

    def get_uploaded_masked_file_url(self, obj):
        request = self.context.get('request')
        if request and obj.masked_file and hasattr(obj.masked_file, 'url'):
            return request.build_absolute_uri(obj.masked_file.url)
        return None
    
    def get_uploaded_file_url(self, obj):
        request = self.context.get('request')
        if request and obj.uploaded_file and hasattr(obj.uploaded_file, 'url'):
            return request.build_absolute_uri(obj.uploaded_file.url)
        return None

    def get_uploaded_processed_seat_image_url(self, obj):
        request = self.context.get('request')
        if request and obj.processed_seat_image and hasattr(obj.processed_seat_image, 'url'):
            return request.build_absolute_uri(obj.processed_seat_image.url)
        return None
    
    def get_uploaded_seat_image_url(self, obj):
        request = self.context.get('request')
        if request and obj.uploaded_seat_image and hasattr(obj.uploaded_seat_image, 'url'):
            return request.build_absolute_uri(obj.uploaded_seat_image.url)
        return None

class TicketPostSerializer(serializers.ModelSerializer):
    ticket = serializers.SerializerMethodField()  # Custom method for ticket serialization

    class Meta:
        model = TicketPost
        fields = "__all__"

    def get_ticket(self, obj):
        """Ensure context is passed to nested TicketSerializer"""
        return TicketSerializer(obj.ticket, context=self.context).data
