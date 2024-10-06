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
        try:
            ticket = Ticket.objects.get(id=ticket_id)
            conversation = Conversation.objects.get(ticket=ticket)
            user = request.user

            # Allow transferee to join if they are already in the conversation
            if not conversation.can_join_new(user):
                if not conversation.can_join_old(user):
                    return Response({"detail": "Conversation full or already joined."}, status=status.HTTP_403_FORBIDDEN)
            
            if conversation.can_join_new(user):
                conversation.transferee = user
                conversation.save()
                # Return masked file and seat image for the transferee
                return Response({
                    "detail": "You have joined the conversation.",
                    "masked_file": ticket.masked_file.url if ticket.masked_file else None,
                    "uploaded_seat_image": ticket.uploaded_seat_image.url if ticket.uploaded_seat_image else None
                }, status=status.HTTP_200_OK)

            return Response({"detail": "You have joined the conversation."}, status=status.HTTP_200_OK)

        except Ticket.DoesNotExist:
            return Response({"detail": "Ticket not found."}, status=status.HTTP_404_NOT_FOUND)
        except Conversation.DoesNotExist:
            return Response({"detail": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)

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
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            user = request.user

            if user == conversation.owner:
                conversation.is_transfer_intent = True
            elif user == conversation.transferee:
                conversation.is_acceptance_intent = True
            else:
                return Response({"detail": "Invalid user."}, status=status.HTTP_403_FORBIDDEN)

            # If both transfer and acceptance intent are marked, process the transfer completion
            if conversation.transfer_complete():
                # Fetch the owner's UserProfile
                transferor_profile = UserProfile.objects.get(user=conversation.owner)

                # Return the bank account and bank name from the owner's UserProfile
                return Response({
                    "detail": "Transfer completed.",
                    "bank_account": transferor_profile.bank_account,
                    "bank_name": transferor_profile.bank_name
                }, status=status.HTTP_200_OK)

            conversation.save()
            return Response({"detail": "Intent marked."}, status=status.HTTP_200_OK)

        except Conversation.DoesNotExist:
            return Response({"detail": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)
class TransferCompleteView(APIView):
    @swagger_auto_schema(
        operation_id="양도 완료 처리",
        operation_description="양도 절차가 완료되면 티켓 상태를 변경하고, 양도자와 양수자의 프로필을 업데이트합니다.",
        responses={
            200: "Transfer completed.",
            404: "Conversation or profiles not found.",
            400: "Invalid state for transfer completion."
        }
    )
    def post(self, request, conversation_id):
        try:
            # Get the conversation based on the provided ID
            conversation = Conversation.objects.get(id=conversation_id)

            # Retrieve profiles of transferee and owner (transferor)
            transferee_profile = UserProfile.objects.get(user=conversation.transferee)
            transferor_profile = UserProfile.objects.get(user=conversation.owner)
            
            # Get the ticket related to this conversation
            ticket = conversation.ticket

            # Save the profiles to ensure any relevant changes (if needed) are persisted
            transferee_profile.save()
            transferor_profile.save()

            # Update ticket status based on the ownership of the ticket
            ticket.status = 'transfer_completed' if ticket.owner == transferor_profile.user else 'received_completed'
            ticket.save()

            # Get the last 4 digits of the transferor's phone number
            phone_last_digits = transferor_profile.phone_last_digits

            # Return the details, including ticket file and phone number
            return Response({
                "detail": "Transfer completed.",
                "ticket_file": ticket.uploaded_file.url,
                "phone_number": phone_last_digits
            }, status=status.HTTP_200_OK)

        except Conversation.DoesNotExist:
            return Response({"detail": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)
        except UserProfile.DoesNotExist:
            return Response({"detail": "User profile not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
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
