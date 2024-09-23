from django.shortcuts import render
from rest_framework.views import APIView
from drf_yasg import openapi
from rest_framework import status
from rest_framework.response import Response
from .models import Ticket
from .serializers import TicketSerializer
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Q
from .request_serializers import TicketListRequestSerializer, TicketDetailRequestSerializer
from user.models import User
from user.request_serializers import SignInRequestSerializer

class TicketListView(APIView):
    @swagger_auto_schema(
        operation_id="티켓 생성",
        operation_description="티켓 양도글을 생성합니다.",
        request_body=TicketListRequestSerializer,
        responses={201: TicketSerializer, 404: "Not Found", 400: "Bad Request"},
    )
    def post(self, request):
        title = request.data.get("title")
        description =request.data.get("description")
        date = request.data.get("date")
        seat = request.data.get("seat")
        booking_details = request.data.get("seat")
        price = request.data.get("price")
        casting = request.data.get("casting")
        uploaded_file = request.data.get("uploaded_file")
        owner_info = request.data.get("owner")
        if not owner_info:
            return Response(
                {"detail": "owner field missing."}, status=status.HTTP_400_BAD_REQUEST
            )
        username = owner_info.get("username")
        password = owner_info.get("password")
        if not username or not password:
            return Response(
                {"detail": "[username, password] fields missing in owner"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not title or not date or not seat or not price or not casting or not uploaded_file:
            return Response(
                {"detail": "content fields missing."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            author = User.objects.get(username=username)
            if not author.check_password(password):
                return Response(
                    {"detail": "Password is incorrect."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ticket = Ticket.objects.create(title=title, description=description, date=date, seat=seat, booking_details=booking_details, price=price, casting=casting, uploaded_file=uploaded_file, author=author)
        except:
            return Response(
                {"detail": "User Not found."}, status=status.HTTP_404_NOT_FOUND
            )


        serializer = TicketSerializer(ticket)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class TicketDetailView(APIView):
    @swagger_auto_schema(
        operation_id="티켓 상세 조회",
        operation_description="티켓 1개의 상세 정보를 조회합니다.",
        responses={200: TicketSerializer, 400: "Bad Request"},
    )
    def get(self, request, ticket_id):
        try:
            ticket = Ticket.objects.get(id=ticket_id)
        except:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = TicketSerializer(instance=ticket)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="티켓 삭제",
        operation_description="티켓 양도글을 삭제합니다.",
        request_body=SignInRequestSerializer,
        responses={204: "No Content", 404: "Not Found", 400: "Bad Request"},
    )
    def delete(self, request, ticket_id):
        try:
            ticket = Ticket.objects.get(id=ticket_id)
        except:
            return Response(
                {"detail": "Post Not found."}, status=status.HTTP_404_NOT_FOUND
            )

        author_info = request.data
        if not author_info:
            return Response(
                {"detail": "author field missing."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        username = author_info.get("username")
        password = author_info.get("password")
        if not username or not password:
            return Response(
                {"detail": "[username, password] fields missing."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            author = User.objects.get(username=username)
            if not author.check_password(password):
                return Response(
                    {"detail": "Password is incorrect."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if ticket.author != author:
                return Response(
                    {"detail": "You are not the author of this post."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        except:
            return Response(
                {"detail": "User Not found."}, status=status.HTTP_404_NOT_FOUND
            )

        ticket.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_id="티켓 수정",
        operation_description="티켓 양도글을 수정합니다.",
        request_body=TicketDetailRequestSerializer,
        responses={200: TicketSerializer, 404: "Not Found", 400: "Bad Request"},
    )
    def put(self, request, post_id):
        try:
            ticket = Ticket.objects.get(id=post_id)
        except:
            return Response(
                {"detail": "Post not found."}, status=status.HTTP_404_NOT_FOUND
            )

        author_info = request.data.get("owner")
        if not author_info:
            return Response(
                {"detail": "author field missing."}, status=status.HTTP_400_BAD_REQUEST
            )
        username = author_info.get("username")
        password = author_info.get("password")
        try:
            author = User.objects.get(username=username)
            if not author.check_password(password):
                return Response(
                    {"detail": "Password is incorrect."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if ticket.author != author:
                return Response(
                    {"detail": "You are not the author of this post."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        except:
            return Response(
                {"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )

        title = request.data.get("title")
        description =request.data.get("description")
        date = request.data.get("date")
        seat = request.data.get("seat")
        booking_details = request.data.get("seat")
        price = request.data.get("price")
        casting = request.data.get("casting")
        uploaded_file = request.data.get("uploaded_file")
        
        if not title or not date or not seat or not price or not casting or not uploaded_file:
            return Response(
                {"detail": "[title, content] fields missing."},
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        ticket.title = title
        ticket.description=description
        ticket.date=date 
        ticket.seat=seat
        ticket.booking_details=booking_details
        ticket.price=price
        ticket.casting=casting
        ticket.uploaded_file=uploaded_file
        
        ticket.save()
        serializer = TicketSerializer(instance=ticket)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class TransferListView(APIView):
    @swagger_auto_schema(
        operation_id="양도 티켓 목록 조회",
        operation_description="사용자가 양도한 티켓 목록을 조회합니다.",
        responses={
            200: TicketSerializer(many=True),
            404: "Not Found",
            400: "Bad Request",
        },
    )
    def get(self, request):
        user = request.user

        # 해당 사용자가 양도한 티켓 목록 (양도 완료 및 양도 중인 티켓 포함)
        transfer_list = Ticket.objects.filter(
            owner=user,
            status__in=['transfer_pending', 'transfer_completed']
        ).order_by('-id')

        if not transfer_list.exists():
            return Response({"detail": "No transferred tickets found."}, status=status.HTTP_404_NOT_FOUND)

        transfer_serializer = TicketSerializer(transfer_list, many=True)
        return Response(transfer_serializer.data, status=status.HTTP_200_OK)


class ReceivedListView(APIView):
    @swagger_auto_schema(
        operation_id="양수 티켓 목록 조회",
        operation_description="사용자가 양수받은 티켓 목록을 조회합니다.",
        responses={
            200: TicketSerializer(many=True),
            404: "Not Found",
            400: "Bad Request",
        },
    )
    def get(self, request):
        user = request.user

        # 해당 사용자가 양수받은 티켓 목록 (양수 완료,양수 중인 티켓 표시)
        received_list = Ticket.objects.filter(
            transferee=user,
            status__in=['transfer_pending', 'received_completed']
        ).order_by('-id')

        if not received_list.exists():
            return Response({"detail": "No received tickets found."}, status=status.HTTP_404_NOT_FOUND)

        received_serializer = TicketSerializer(received_list, many=True)
        return Response(received_serializer.data, status=status.HTTP_200_OK)