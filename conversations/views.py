from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Conversation
from tickets.models import Ticket
from drf_yasg.utils import swagger_auto_schema
from user.models import UserProfile  

class JoinConversationView(APIView):
    @swagger_auto_schema(
        operation_id="대화방 참여",
        operation_description="사용자가 특정 티켓과 연결된 대화방에 참여합니다. 대화방이 가득 차거나 이미 참여한 경우 참여할 수 없습니다.",
        responses={
            200: "You have joined the conversation.",
            403: "Conversation full or already joined.",
            404: "Not Found"
        }
    )
    def post(self, request, ticket_id):
        ticket = Ticket.objects.get(id=ticket_id)
        conversation = Conversation.objects.get(ticket=ticket)
        user = request.user

        if not conversation.can_join(user):
            return Response({"detail": "Conversation full or already joined."}, status=status.HTTP_403_FORBIDDEN)
        
        conversation.transferee = user
        conversation.save()

        return Response({"detail": "You have joined the conversation."}, status=status.HTTP_200_OK)

class TransferIntentView(APIView):
    @swagger_auto_schema(
        operation_id="양도 및 양수 의사 표시",
        operation_description="양도자 또는 양수자가 각각 양도 및 양수 의사를 표시합니다. 둘 다 의사를 표시하면 거래가 완료됩니다.",
        responses={
            200: "Intent marked successfully.",
            403: "Invalid user or permission denied.",
            404: "Conversation not found.",
            400: "Insufficient points."
        }
    )
    def post(self, request, conversation_id):
        conversation = Conversation.objects.get(id=conversation_id)
        user = request.user

        if user == conversation.owner:
            conversation.is_transfer_intent = True
        elif user == conversation.transferee:
            # Check if the transferee has enough points
            if not conversation.check_sufficient_points():
                return Response({"detail": "Insufficient points to complete the transaction."}, status=status.HTTP_400_BAD_REQUEST)
            conversation.is_acceptance_intent = True
        else:
            return Response({"detail": "Invalid user."}, status=status.HTTP_403_FORBIDDEN)

        if conversation.transfer_complete():
            transferee_profile = UserProfile.objects.get(user=conversation.transferee)
            transferor_profile = UserProfile.objects.get(user=conversation.owner)
            ticket = conversation.ticket

            transferee_profile.save()
            transferor_profile.save()

            # 티켓 상태 변경
            ticket.status = 'transfer_completed' if ticket.owner == transferor_profile.user else 'received_completed'
            ticket.save()

            phone_last_digits = transferor_profile.phone_number[-4:]
            return Response({
                "detail": "Transfer completed.",
                "ticket_file": ticket.uploaded_file.url,
                "phone_number": phone_last_digits
            }, status=status.HTTP_200_OK)

        conversation.save()
        return Response({"detail": "Intent marked."}, status=status.HTTP_200_OK)
class LeaveConversationView(APIView):
    @swagger_auto_schema(
        operation_id="대화방 나가기",
        operation_description="양수자가 대화방에서 나가면 새로운 사용자가 대화방에 참여할 수 있습니다. 양수자만 대화방에서 나갈 수 있습니다.",
        responses={
            200: "You have left the conversation. A new user can now join.",
            403: "You are not part of this conversation.",
            404: "Conversation not found."
        }
    )
    def post(self, request, conversation_id):
        conversation = Conversation.objects.get(id=conversation_id)
        user = request.user

        # Only the transferee can leave the conversation
        if conversation.transferee != user:
            return Response({"detail": "You are not part of this conversation."}, status=status.HTTP_403_FORBIDDEN)

        # Reset the transferee and allow a new user to join
        conversation.reset_transferee()

        return Response({"detail": "You have left the conversation. A new user can now join."}, status=status.HTTP_200_OK)
