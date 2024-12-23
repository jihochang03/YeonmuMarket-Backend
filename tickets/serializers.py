from rest_framework import serializers
from .models import Ticket, TicketPost

class TicketSerializer(serializers.ModelSerializer):
    uploaded_masked_file_url = serializers.SerializerMethodField()
    uploaded_file_url = serializers.SerializerMethodField()
    uploaded_processed_seat_image_url = serializers.SerializerMethodField()
    uploaded_seat_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = "__all__"

    def get_uploaded_masked_file_url(self, obj):
        request = self.context.get('request')
        if obj.masked_file_url:  # URL 필드 값이 존재하는지 확인
            if request:
                return request.build_absolute_uri(obj.masked_file_url)
            return obj.masked_file_url
        return None

    def get_uploaded_file_url(self, obj):
        request = self.context.get('request')
        if obj.uploaded_file_url:
            if request:
                return request.build_absolute_uri(obj.uploaded_file_url)
            return obj.uploaded_file_url
        return None

    def get_uploaded_processed_seat_image_url(self, obj):
        request = self.context.get('request')
        if obj.processed_seat_image_url:
            if request:
                return request.build_absolute_uri(obj.processed_seat_image_url)
            return obj.processed_seat_image_url
        return None

    def get_uploaded_seat_image_url(self, obj):
        request = self.context.get('request')
        if obj.uploaded_seat_image_url:
            if request:
                return request.build_absolute_uri(obj.uploaded_seat_image_url)
            return obj.uploaded_seat_image_url
        return None


class TicketPostSerializer(serializers.ModelSerializer):
    ticket = serializers.SerializerMethodField()  # Custom method for ticket serialization

    class Meta:
        model = TicketPost
        fields = "__all__"

    def get_ticket(self, obj):
        """Ensure context is passed to nested TicketSerializer"""
        return TicketSerializer(obj.ticket, context=self.context).data

