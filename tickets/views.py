from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from .models import Ticket, TransferRequest, TransferHistory
from .serializers import TicketSerializer, TransferRequestSerializer, TransferHistorySerializer
from .signals import notify_owner


class TicketListCreateAPIView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TicketSerializer

    @swagger_auto_schema(
        operation_summary="Retrieve tickets owned by the authenticated user",
        responses={200: TicketSerializer(many=True)}
    )
    def get_queryset(self):
        return Ticket.objects.filter(owner=self.request.user)

    @swagger_auto_schema(
        operation_summary="Create a new ticket",
        responses={201: TicketSerializer}
    )
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TicketRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TicketSerializer

    @swagger_auto_schema(
        operation_summary="Retrieve, update, or delete a ticket",
        responses={200: TicketSerializer}
    )
    def get_queryset(self):
        return Ticket.objects.filter(owner=self.request.user)


class TransferRequestCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Create a transfer request",
        request_body=TransferRequestSerializer,
        responses={201: TransferRequestSerializer}
    )
    def post(self, request, *args, **kwargs):
        serializer = TransferRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(buyer=request.user)
            ticket = serializer.validated_data['ticket']
            notify_owner.send(sender=self.__class__, ticket=ticket, requestor=self.request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransferHistoryListAPIView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TransferHistorySerializer

    @swagger_auto_schema(
        operation_summary="List transfer history for authenticated user",
        responses={200: TransferHistorySerializer(many=True)}
    )
    def get_queryset(self):
        return TransferHistory.objects.filter(transferee=self.request.user)

