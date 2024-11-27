from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Conversation
from tickets.models import Ticket
from drf_yasg.utils import swagger_auto_schema
from user.models import UserProfile
from payments.models import Account
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from rest_framework.permissions import AllowAny
from django.shortcuts import redirect
from django.urls import reverse
from rest_framework import status
from django.http import HttpResponseRedirect


@method_decorator(csrf_exempt, name='dispatch')
class JoinConversationView(APIView):
    permission_classes = [AllowAny]

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
        print(f"[JoinConversationView] POST called with ticket_id: {ticket_id}")
        try:
            # Check if user is authenticated
            if not request.user.is_authenticated:
                print(f"[JoinConversationView] User not authenticated. Redirecting to Kakao login.")
                kakao_login_url = f"{reverse('user:kakao-login')}?next=/chat/{ticket_id}/join"
    
                # Return JSON response with redirect URL
                return Response(
                {
                    "detail": "User not authenticated. Redirecting to Kakao login.",
                    "redirect_url": kakao_login_url
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

            ticket = Ticket.objects.get(id=ticket_id)
            print(f"[JoinConversationView] Ticket found: {ticket}")
            conversation, created = Conversation.objects.get_or_create(ticket=ticket, defaults={'owner': ticket.owner})
            print(f"[JoinConversationView] Conversation {'created' if created else 'retrieved'}: {conversation}")
            user = request.user
            
            # Redirect to chat page if the user is the owner of the conversation
            if user == conversation.owner:
                print(f"[JoinConversationView] Conversation is yours: {conversation.owner}")
                chat_url = f"http://localhost:5173/chat/{ticket_id}"  # Adjust the URL as per your frontend routing
                return Response({"detail": "Conversation is yours.", "redirect_url": chat_url},status=status.HTTP_200_OK)
            
            elif conversation.transferee and conversation.transferee != user:
                print(f"[JoinConversationView] Conversation full or already joined by another user: {conversation.transferee}")
                return Response({"detail": "Conversation full or already joined."}, status=status.HTTP_403_FORBIDDEN)

            elif not conversation.transferee:
                conversation.transferee = user
                conversation.save()
                print(f"[JoinConversationView] User {user} joined the conversation {conversation}")
                # Return masked file and seat image for the transferee
                return Response({
                    "detail": "You have joined the conversation.",
                    "conversation_id": conversation.id,
                    "uploaded_seat_image": ticket.uploaded_seat_image.url if ticket.uploaded_seat_image else None
                }, status=status.HTTP_200_OK)
            
            print(f"[JoinConversationView] User {user} rejoined the conversation {conversation}")
            return Response({"detail": "You have joined the conversation."}, status=status.HTTP_200_OK)

        except Ticket.DoesNotExist:
            print(f"[JoinConversationView] Ticket with id {ticket_id} does not exist.")
            return Response({"detail": "Ticket not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"[JoinConversationView] An unexpected error occurred: {str(e)}")
            return Response({"detail": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class ConversationDetailView(APIView):

    @swagger_auto_schema(
        operation_id="대화방 상세 정보",
        operation_description="특정 티켓과 사용자에 대한 대화방의 세부 정보를 가져옵니다.",
        responses={
            200: "Conversation data retrieved successfully.",
            403: "You are not part of this conversation.",
            404: "Conversation or Ticket not found."
        }
    )
    def get(self, request, ticket_id):
        print(f"[ConversationDetailView] GET called with ticket_id: {ticket_id}")
        try:
            user = request.user
            print(f"[ConversationDetailView] Request user: {user}, is_authenticated: {user.is_authenticated}")
            ticket = Ticket.objects.get(id=ticket_id)
            print(f"[ConversationDetailView] Ticket found: {ticket}")
            conversation = Conversation.objects.get(ticket=ticket)
            print(f"[ConversationDetailView] Conversation retrieved: {conversation}")

            # Check if the user is part of the conversation
            if user != conversation.owner and user != conversation.transferee:
                print(f"[ConversationDetailView] User {user} is not part of the conversation {conversation}")
                return Response({"detail": "You are not part of this conversation."}, status=status.HTTP_403_FORBIDDEN)

            # Prepare the data to return
            data = {
                "conversation_id": conversation.id,
                "ticket_id": ticket.id,
                "title": ticket.title,
                "transaction_step": conversation.transaction_step,
                "user_role": "seller" if user == conversation.owner else "buyer",
                "masked_file_url": None,
                "seat_image_url": ticket.uploaded_seat_image.url if ticket.uploaded_seat_image else None,
                "bank_account": None,
                "bank_name": None,
                "account_holder": None,
                "ticket_file_url": None,
                "phone_last_digits": None,
                "buyer_name": conversation.transferee.username if conversation.transferee else '',
                "seller_name": conversation.owner.username,
            }
            print(f"[ConversationDetailView] Response data prepared: {data}")

            # Include bank account info if transfer intents are confirmed
            if conversation.transaction_step >= 2:
                data["masked_file_url"] = ticket.masked_file.url if ticket.masked_file else None

                try:
                    transferor_account = Account.objects.get(user=conversation.owner)
                    print(f"[ConversationDetailView] Transferor account: {transferor_account}")
                    data["bank_account"] = transferor_account.bank_account
                    data["bank_name"] = transferor_account.bank_name
                    data["account_holder"] = transferor_account.user.username  # 또는 이름 필드 사용
                except Account.DoesNotExist:
                    print("[ConversationDetailView] No account found for the transferor.")
                    data["bank_account"] = None
                    data["bank_name"] = None
                    data["account_holder"] = None

            # Include ticket file and phone number if transfer is complete
            if conversation.transaction_step >= 4:
                data["ticket_file_url"] = ticket.uploaded_file.url if ticket.uploaded_file else None
                data["seat_image_url"] = ticket.uploaded_seat_image.url if ticket.uploaded_seat_image else None
                transferor_profile = UserProfile.objects.get(user=conversation.owner)
                data["phone_last_digits"] = transferor_profile.phone_last_digits

            return Response(data, status=status.HTTP_200_OK)

        except Ticket.DoesNotExist:
            print(f"[ConversationDetailView] Ticket with id {ticket_id} does not exist.")
            return Response({"detail": "Ticket not found."}, status=status.HTTP_404_NOT_FOUND)
        except Conversation.DoesNotExist:
            print(f"[ConversationDetailView] Conversation for ticket {ticket} does not exist.")
            return Response({"detail": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"[ConversationDetailView] An unexpected error occurred: {str(e)}")
            return Response({"detail": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TransferIntentView(APIView):
    @swagger_auto_schema(
        operation_id="양도 및 양수 의사 표시",
        operation_description="양도자 또는 양수자가 각각 양도 및 양수 의사를 표시합니다.",
        responses={
            200: "Intent marked successfully.",
            403: "Invalid user or permission denied.",
            404: "Conversation not found.",
            400: "Invalid state."
        }
    )
    def post(self, request, ticket_id):
        print(f"[TransferIntentView] POST called with ticket_id: {ticket_id}")
        try:
            user = request.user
            print(f"[TransferIntentView] Request user: {user}, is_authenticated: {user.is_authenticated}")
            ticket = Ticket.objects.get(id=ticket_id)
            print(f"[[TransferIntentView] Ticket found: {ticket}")
            conversation = Conversation.objects.get(ticket=ticket)
            print(f"[TransferIntentView] Conversation found: {conversation}")

            if user == conversation.transferee:
                print(f"[TransferIntentView] User {user} is transferee")
                if conversation.transaction_step != 0:
                    print(f"[TransferIntentView] Invalid state for buyer to confirm intent: transaction_step={conversation.transaction_step}")
                    return Response({"detail": "Invalid state for buyer to confirm intent."}, status=status.HTTP_400_BAD_REQUEST)
                conversation.is_acceptance_intent = True
                conversation.transaction_step = 1  # Buyer confirmed intent
            elif user == conversation.owner:
                print(f"[TransferIntentView] User {user} is owner")
                if conversation.transaction_step != 1:
                    print(f"[TransferIntentView] Invalid state for seller to confirm intent: transaction_step={conversation.transaction_step}")
                    return Response({"detail": "Invalid state for seller to confirm intent."}, status=status.HTTP_400_BAD_REQUEST)
                conversation.is_transfer_intent = True
                conversation.transaction_step = 2  # Seller confirmed intent
            else:
                print(f"[TransferIntentView] Invalid user: {user}")
                return Response({"detail": "Invalid user."}, status=status.HTTP_403_FORBIDDEN)

            conversation.save()
            print(f"[TransferIntentView] Conversation updated: {conversation}")

            # If both intents are confirmed, include bank account info
            if conversation.is_transfer_intent and conversation.is_acceptance_intent:
                transferor_profile = UserProfile.objects.get(user=conversation.owner)
                print(f"[TransferIntentView] Both intents confirmed. Transferor profile: {transferor_profile}")
                return Response({
                    "detail": "Both intents confirmed.",
                    "bank_account": transferor_profile.bank_account,
                    "bank_name": transferor_profile.bank_name,
                    "account_holder": transferor_profile.bank_account_holder
                }, status=status.HTTP_200_OK)

            return Response({"detail": "Intent marked."}, status=status.HTTP_200_OK)

        except Conversation.DoesNotExist:
            print(f"[TransferIntentView] Conversation with id {ticket_id} does not exist.")
            return Response({"detail": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"[TransferIntentView] An unexpected error occurred: {str(e)}")
            return Response({"detail": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentCompleteView(APIView):

    @swagger_auto_schema(
        operation_id="입금 완료 처리",
        operation_description="양수자가 입금 완료를 확인합니다.",
        responses={
            200: "Payment marked as completed.",
            403: "Invalid user or permission denied.",
            404: "Conversation not found.",
            400: "Invalid state."
        }
    )
    def post(self, request, ticket_id):
        print(f"[PaymentCompleteView] POST called with ticket_id: {ticket_id}")
        try:
            user = request.user
            print(f"[PaymentCompleteView] Request user: {user}, is_authenticated: {user.is_authenticated}")
            ticket = Ticket.objects.get(id=ticket_id)
            print(f"[PaymentCompleteView] Ticket found: {ticket}")
            conversation = Conversation.objects.get(ticket=ticket)
            print(f"[PaymentCompleteView] Conversation found: {conversation}")

            if user != conversation.transferee:
                print(f"[PaymentCompleteView] User {user} is not the transferee")
                return Response({"detail": "Only the buyer can confirm payment."}, status=status.HTTP_403_FORBIDDEN)

            if conversation.transaction_step != 2:
                print(f"[PaymentCompleteView] Invalid state to confirm payment: transaction_step={conversation.transaction_step}")
                return Response({"detail": "Invalid state to confirm payment."}, status=status.HTTP_400_BAD_REQUEST)

            conversation.transaction_step = 3  # Payment completed
            conversation.save()
            print(f"[PaymentCompleteView] Conversation updated: {conversation}")

            return Response({"detail": "Payment marked as completed."}, status=status.HTTP_200_OK)

        except Conversation.DoesNotExist:
            print(f"[PaymentCompleteView] Conversation with id {ticket_id} does not exist.")
            return Response({"detail": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"[PaymentCompleteView] An unexpected error occurred: {str(e)}")
            return Response({"detail": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConfirmReceiptView(APIView):

    @swagger_auto_schema(
        operation_id="입금 확인 및 거래 완료",
        operation_description="양도자가 입금을 확인하고 거래를 완료합니다.",
        responses={
            200: "Receipt confirmed. Transfer completed.",
            403: "Invalid user or permission denied.",
            404: "Conversation not found.",
            400: "Invalid state."
        }
    )
    def post(self, request, ticket_id):
        print(f"[ConfirmReceiptView] POST called with ticket_id: {ticket_id}")
        try:
            user = request.user
            print(f"[ConfirmReceiptView] Request user: {user}, is_authenticated: {user.is_authenticated}")
            ticket = Ticket.objects.get(id=ticket_id)
            print(f"[ConfirmReceiptView] Ticket found: {ticket}")
            conversation = Conversation.objects.get(ticket=ticket)
            print(f"[ConfirmReceiptView] Conversation found: {conversation}")

            if user != conversation.owner:
                print(f"[ConfirmReceiptView] User {user} is not the owner")
                return Response({"detail": "Only the seller can confirm receipt."}, status=status.HTTP_403_FORBIDDEN)

            if conversation.transaction_step != 3:
                print(f"[ConfirmReceiptView] Invalid state to confirm receipt: transaction_step={conversation.transaction_step}")
                return Response({"detail": "Invalid state to confirm receipt."}, status=status.HTTP_400_BAD_REQUEST)

            conversation.transaction_step = 4  # Transfer completed
            conversation.save()
            print(f"[ConfirmReceiptView] Conversation updated: {conversation}")

            # Update ticket status
            ticket = conversation.ticket
            ticket.status = 'transfer_completed'
            ticket.save()
            print(f"[ConfirmReceiptView] Ticket updated: {ticket}")

            # Return ticket file and seller's phone last digits
            transferor_profile = UserProfile.objects.get(user=conversation.owner)
            phone_last_digits = transferor_profile.phone_last_digits
            print(f"[ConfirmReceiptView] Transferor profile: {transferor_profile}")

            return Response({
                "detail": "Transfer completed.",
                "ticket_file_url": ticket.uploaded_file.url,
                "phone_last_digits": phone_last_digits
            }, status=status.HTTP_200_OK)

        except Conversation.DoesNotExist:
            print(f"[ConfirmReceiptView] Conversation with id {ticket_id} does not exist.")
            return Response({"detail": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"[ConfirmReceiptView] An unexpected error occurred: {str(e)}")
            return Response({"detail": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        print(f"[LeaveConversationView] POST called with conversation_id: {conversation_id}")
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            print(f"[LeaveConversationView] Conversation found: {conversation}")
            user = request.user
            print(f"[LeaveConversationView] Request user: {user}, is_authenticated: {user.is_authenticated}")

            # Only the transferee can leave the conversation
            if conversation.transferee != user:
                print(f"[LeaveConversationView] User {user} is not the transferee")
                return Response({"detail": "You are not part of this conversation."}, status=status.HTTP_403_FORBIDDEN)

            # Reset the transferee and transaction step
            conversation.transferee = None
            conversation.transaction_step = 0
            conversation.is_transfer_intent = False
            conversation.is_acceptance_intent = False
            conversation.save()
            print(f"[LeaveConversationView] Conversation updated after user left: {conversation}")

            return Response({"detail": "You have left the conversation. A new user can now join."}, status=status.HTTP_200_OK)

        except Conversation.DoesNotExist:
            print(f"[LeaveConversationView] Conversation with id {conversation_id} does not exist.")
            return Response({"detail": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"[LeaveConversationView] An unexpected error occurred: {str(e)}")
            return Response({"detail": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
