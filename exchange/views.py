from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Exchange
from tickets.models import Ticket, TicketPost
from tickets.serializers import TicketSerializer, TicketPostSerializer
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
from django.http import HttpResponse, JsonResponse
from django.conf import settings
import os
from drf_yasg import openapi

# Create your @method_decorator(csrf_exempt, name='dispatch')
class JoinExchangeView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id="대화방 참여",
        operation_description="사용자가 특정 티켓과 연결된 대화방에 참여합니다. 대화방이 가득 차거나 이미 참여한 경우 참여할 수 없습니다.",
        responses={
            200: "You have joined the Exchange.",
            403: "Exchange full or already joined.",
            404: "Not Found",
            400: "Bad Request"
        }
    )
    def post(self, request, ticket_id):
        print(f"[JoinExchangeView] POST called with ticket_id: {ticket_id}")
        try:
            # Get my_ticket_number from request data
            my_ticket_number = request.data.get("my_ticket_number")
            if not my_ticket_number:
                print("[JoinExchangeView] my_ticket_number is missing.")
                return Response({"detail": "Ticket number is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Check if user is authenticated
            if not request.user.is_authenticated:
                print(f"[JoinExchangeView] User not authenticated. Redirecting to Kakao login.")
                kakao_login_url = f"{reverse('user:kakao-login')}?next=/chat/{ticket_id}/join"
                return Response(
                    {
                        "detail": "User not authenticated. Redirecting to Kakao login.",
                        "redirect_url": kakao_login_url,
                    },
                    status=status.HTTP_401_UNAUTHORIZED
                )

            ticket_1 = Ticket.objects.get(id=ticket_id)
            print(f"[JoinExchangeView] Ticket found: {ticket_1}")
            ticket_2= Ticket.objects.get(id=my_ticket_number)
            print(f"[JoinExchangeView] Ticket found: {ticket_2}")
          

            # Retrieve or create an Exchange object
            exchange, created = Exchange.objects.get_or_create(
                ticket_1=ticket_1, ticket_2=ticket_2, defaults={'owner': ticket_1.owner}
            )
            print(f"[JoinExchangeView] Exchange {'created' if created else 'retrieved'}: {exchange}")

            user = request.user

            # If the user is the owner of the Exchange
            if user == exchange.owner:
                print(f"[JoinExchangeView] Exchange is yours: {exchange.owner}")
                exchange_url = f"https://www.yeonmu.shop/exchange/{ticket_id}"  # Adjust the URL as per your frontend routing
                return Response({"detail": "Exchange is yours.", "redirect_url": exchange_url}, status=status.HTTP_200_OK)

            # If the Exchange is full
            if exchange.transferee and exchange.transferee != user:
                print(f"[JoinExchangeView] Exchange full or already joined by another user: {exchange.transferee}")
                return Response({"detail": "Exchange full or already joined."}, status=status.HTTP_403_FORBIDDEN)

            # If the user is already the transferee
            if user == exchange.transferee:
                print(f"[JoinExchangeView] User is already part of the Exchange: {exchange.transferee}")
                exchange_url = f"https://www.yeonmu.shop/exchange/{ticket_id}"  # Adjust the URL as per your frontend routing
                return Response({"detail": "You are already part of the Exchange.", "redirect_url": exchange_url}, status=status.HTTP_200_OK)

            # If the Exchange is not full, assign transferee and update status
            if not exchange.transferee:
                exchange.transferee = user
                exchange.ticket_2 = ticket_2
                exchange.transaction_step=1
                exchange.save()

                ticket_1.transferee = user
                ticket_1.status_exchange = 'exchange_pending'  # Update status for exchange
                ticket_1.save()
                
                ticket_2.transferee = exchange.owner
                ticket_2.status_exchange = 'exchange_pending'  # Update status for exchange
                ticket_2.save()

                print(f"[JoinExchangeView] User {user} joined the Exchange {exchange}")
                exchange_url = f"https://www.yeonmu.shop/exchange/{ticket_id}"  # Adjust the URL as per your frontend routing
                return Response({
                    "detail": "You have joined the Exchange.",
                    "redirect_url": exchange_url,
                }, status=status.HTTP_200_OK)

        except Ticket.DoesNotExist:
            print(f"[JoinExchangeView] Ticket with id {ticket_id} does not exist.")
            return Response({"detail": "Ticket not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"[JoinExchangeView] An unexpected error occurred: {str(e)}")
            return Response({"detail": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ExchangeDetailView(APIView):

    @swagger_auto_schema(
        operation_id="대화방 상세 정보",
        operation_description="특정 티켓과 사용자에 대한 대화방의 세부 정보를 가져옵니다.",
        responses={
            200: "Exchange data retrieved successfully.",
            403: "You are not part of this Exchange.",
            404: "Exchange or Ticket not found."
        }
    )
    def get(self, request, ticket_id):
        print(f"[ExchangeDetailView] GET called with ticket_id: {ticket_id}")
        try:
            user = request.user
            print(f"[ExchangeDetailView] Request user: {user}, is_authenticated: {user.is_authenticated}")

            # Ticket 가져오기
            ticket_1 = Ticket.objects.get(id=ticket_id)
            
            exchange = Exchange.objects.get(ticket_1=ticket_1)
            print(f"[ExchangeDetailView] Exchange retrieved: {exchange}")
            
            ticket_2=exchange.ticket_2

            # TicketPost 가져오기
            try:
                ticket_post_1 = TicketPost.objects.get(ticket=ticket_1)  # `ticket_id`를 `ticket`으로 연결
            except TicketPost.DoesNotExist:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
              
            ticket_post_1.ticket = ticket_1
              
            # TicketPost 가져오기
            try:
                ticket_post_2 = TicketPost.objects.get(ticket=ticket_2)  # `ticket_id`를 `ticket`으로 연결
            except TicketPost.DoesNotExist:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

            # TicketPost의 ticket 정보 동기화
            ticket_post_2.ticket = ticket_2
  
            # 직렬화
            serializer_1 = TicketPostSerializer(ticket_post_1, context={'request': request})
            serializer_2 = TicketPostSerializer(ticket_post_1, context={'request': request})

            # Account 가져오기
            account_1 = Account.objects.get(user=ticket_1.owner)
            account_2 = Account.objects.get(user=exchange.ticket_2.owner)


            # Check if the user is part of the Exchange
            if user != exchange.owner and user != exchange.transferee:
                print(f"[ExchangeDetailView] User {user} is not part of the Exchange {exchange}")
                return Response({"detail": "You are not part of this Exchange."}, status=status.HTTP_403_FORBIDDEN)

            # Prepare the data to return
            data = {
                "Exchange_id": exchange.id,
                "transaction_step": exchange.transaction_step,
                "user_role": "seller" if user == exchange.owner else "buyer",
                "bank_account_seller": account_1.bank_account,
                "bank_account_buyer": account_2.bank_account,
                "bank_name_seller": account_1.bank_name,
                "bank_name_buyer": account_2.bank_name,
                "account_holder_seller": account_1.account_holder,
                "account_holder_buyer": account_2.account_holder,
                "buyer_name": exchange.transferee.username if exchange.transferee else '',
                "seller_name": exchange.owner.username,
            }
            response_data = {
            "exchange_data": data,
            "ticket_post_data_seller": serializer_1.data,
            "ticket_post_data_buyer": serializer_2.data,
            }
            print(f"[ExchangeDetailView] Response data prepared: {response_data}")
            return Response(response_data, status=status.HTTP_200_OK)

        except Ticket.DoesNotExist:
            print(f"[ExchangeDetailView] Ticket with id {ticket_id} does not exist.")
            return Response({"detail": "Ticket not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exchange.DoesNotExist:
            print(f"[ExchangeDetailView] Exchange for ticket {ticket_1} does not exist.")
            return Response({"detail": "Exchange not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"[ExchangeDetailView] An unexpected error occurred: {str(e)}")
            return Response({"detail": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def fetch_image(request):
    """
    Fetches an image from a given URL path and returns it.
    """
    image_url = request.GET.get("url")  # 프론트엔드에서 전달받은 URL
    if not image_url:
        return JsonResponse({"error": "URL parameter is required."}, status=400)

    # MEDIA_ROOT 기준으로 절대 경로 계산
    image_path = os.path.join(settings.MEDIA_ROOT, image_url.replace(settings.MEDIA_URL, ""))
    
    if not os.path.exists(image_path):
        return JsonResponse({"error": "Image not found."}, status=404)

    # 이미지 파일 읽기 및 반환
    with open(image_path, "rb") as image_file:
        return HttpResponse(image_file.read(), content_type="image/jpeg")

class TransferIntentView(APIView):
    @swagger_auto_schema(
        operation_id="양도 및 양수 의사 표시",
        operation_description="양도자 또는 양수자가 각각 양도 및 양수 의사를 표시합니다.",
        responses={
            200: "Intent marked successfully.",
            403: "Invalid user or permission denied.",
            404: "exchange not found.",
            400: "Invalid state."
        }
    )
    def post(self, request, ticket_id):
        print(f"[TransferIntentView] POST called with ticket_id: {ticket_id}")
        try:
            user = request.user
            print(f"[TransferIntentView] Request user: {user}, is_authenticated: {user.is_authenticated}")
            ticket_1 = Ticket.objects.get(id=ticket_id)
            print(f"[[TransferIntentView] Ticket found: {ticket_1}")
            exchange = Exchange.objects.get(ticket_1=ticket_1)
            print(f"[TransferIntentView] exchange found: {exchange}")

            if user == exchange.transferee:
                print(f"[TransferIntentView] User {user} is transferee")
                if exchange.transaction_step != 1:
                    print(f"[TransferIntentView] Invalid state for buyer to confirm intent: transaction_step={exchange.transaction_step}")
                    return Response({"detail": "Invalid state for buyer to confirm intent."}, status=status.HTTP_400_BAD_REQUEST)
                exchange.is_acceptance_intent = True
            elif user == exchange.owner:
                print(f"[TransferIntentView] User {user} is owner")
                if exchange.transaction_step != 1:
                    print(f"[TransferIntentView] Invalid state for seller to confirm intent: transaction_step={exchange.transaction_step}")
                    return Response({"detail": "Invalid state for seller to confirm intent."}, status=status.HTTP_400_BAD_REQUEST)
                exchange.is_transfer_intent = True
            else:
                print(f"[TransferIntentView] Invalid user: {user}")
                return Response({"detail": "Invalid user."}, status=status.HTTP_403_FORBIDDEN)
            exchange.save()
            print(f"[TransferIntentView] exchange updated: {exchange}")

            # If both intents are confirmed, include bank account info
            if exchange.is_transfer_intent and exchange.is_acceptance_intent:
                print(f"[TransferIntentView] exchange okay: {exchange}")
                exchange.transaction_step = 2 
                exchange.save()
                seller_account = Account.objects.get(user=exchange.owner)
                buyer_account = Account.objects.get(user=exchange.transferee)
                print(f"[TransferIntentView] Both intents confirmed. Transferor profile: {seller_account}, {buyer_account}")
                return Response({
                    "detail": "Both intents confirmed.",
                    "transaction_step": 2,
                    "bank_account_seller": seller_account.bank_account,
                    "bank_name_seller": seller_account.bank_name,
                    "account_holder_seller": seller_account.account_holder,
                    "bank_account_buyer": buyer_account.bank_account,
                    "bank_name_buyer": buyer_account.bank_name,
                    "account_holder_buyer": buyer_account.account_holder,
                }, status=status.HTTP_200_OK)

            return Response({"detail": "Intent marked.","transaction_step": 0,}, status=status.HTTP_200_OK)

        except exchange.DoesNotExist:
            print(f"[TransferIntentView] exchange with id {ticket_id} does not exist.")
            return Response({"detail": "exchange not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"[TransferIntentView] An unexpected error occurred: {str(e)}")
            return Response({"detail": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class ConfirmDifferenceView(APIView):

    @swagger_auto_schema(
        operation_id="차액 확정",
        operation_description="양도자와 양수자가 합의한 차액을 확정합니다. (transaction_step=1 → transaction_step=2)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'differenceAmount': openapi.Schema(type=openapi.TYPE_NUMBER, description='차액 금액'),
                'payDirection': openapi.Schema(type=openapi.TYPE_STRING, description='buyerToSeller / sellerToBuyer / none'),
            },
            required=['differenceAmount', 'payDirection']
        ),
        responses={
            200: "차액이 확정되어 transaction_step=2 로 변경되었습니다.",
            400: "Invalid state.",
            403: "권한이 없는 사용자.",
            404: "존재하지 않는 Exchange.",
            500: "서버 에러",
        }
    )
    def post(self, request, ticket_id):
        print(f"[ConfirmDifferenceView] POST called with ticket_id: {ticket_id}")
        try:
            user = request.user
            print(f"[ConfirmDifferenceView] Request user: {user}, is_authenticated: {user.is_authenticated}")

            # 1. Ticket 및 Exchange 찾기
            ticket = Ticket.objects.get(id=ticket_id)
            print(f"[ConfirmDifferenceView] Ticket found: {ticket}")
            exchange = Exchange.objects.get(ticket_1=ticket)  # 혹은 ticket_2 사용
            print(f"[ConfirmDifferenceView] Exchange found: {exchange}")

            # 2. transaction_step이 1인지 확인
            if exchange.transaction_step != 2:
                print(f"[ConfirmDifferenceView] Invalid state for confirming difference: transaction_step={exchange.transaction_step}")
                return Response({"detail": "Invalid state to confirm difference."},
                                status=status.HTTP_400_BAD_REQUEST)

            # (선택) buyer/seller 구분해서 접근 권한을 줄 수도 있음.
            # 여기서는 단순히 transaction_step으로만 제한.

            # 3. 바디에서 차액 정보 가져오기
            difference_amount = request.data.get('differenceAmount', 0)
            pay_direction = request.data.get('payDirection', 'none')

            # 4. Exchange 모델에 저장(옵션)
            exchange.difference_amount = difference_amount
            exchange.pay_direction = pay_direction

            # 5. transaction_step=2로 변경 후 저장
            exchange.transaction_step = 3
            exchange.save()
            print(f"[ConfirmDifferenceView] exchange updated: {exchange}")

            return Response({
                "detail": "차액이 확정되었습니다.",
                "transaction_step": 3,
                "difference_amount": difference_amount,
                "pay_direction": pay_direction
            }, status=status.HTTP_200_OK)

        except Ticket.DoesNotExist:
            print(f"[ConfirmDifferenceView] Ticket with id={ticket_id} does not exist.")
            return Response({"detail": "ticket not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exchange.DoesNotExist:
            print(f"[ConfirmDifferenceView] Exchange with ticket_id={ticket_id} does not exist.")
            return Response({"detail": "exchange not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            print(f"[ConfirmDifferenceView] An unexpected error occurred: {str(e)}")
            return Response({"detail": f"An error occurred: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentCompleteView(APIView):

    @swagger_auto_schema(
        operation_id="입금 완료 처리",
        operation_description="(transaction_step=2) → 구매자가 입금 완료를 확인하면 transaction_step=3으로 변경합니다.",
        responses={
            200: "입금 완료 처리됨. transaction_step=3",
            400: "Invalid state.",
            403: "Invalid user or permission denied.",
            404: "exchange not found.",
            500: "서버 에러",
        }
    )
    def post(self, request, ticket_id):
        print(f"[PaymentCompleteView] POST called with ticket_id: {ticket_id}")
        try:
            user = request.user
            print(f"[PaymentCompleteView] Request user: {user}, is_authenticated: {user.is_authenticated}")

            # 1. Ticket 및 Exchange 찾기
            ticket = Ticket.objects.get(id=ticket_id)
            print(f"[PaymentCompleteView] Ticket found: {ticket}")
            exchange = Exchange.objects.get(ticket_1=ticket)  # 혹은 ticket_2
            print(f"[PaymentCompleteView] exchange found: {exchange}")

            # 2. 권한 체크(양수자만 가능)
            if user != exchange.transferee:
                print(f"[PaymentCompleteView] User {user} is not the transferee")
                return Response({"detail": "Only the buyer can confirm payment."},
                                status=status.HTTP_403_FORBIDDEN)

            # 3. transaction_step이 2인지 확인
            if exchange.transaction_step != 3:
                print(f"[PaymentCompleteView] Invalid state to confirm payment: transaction_step={exchange.transaction_step}")
                return Response({"detail": "Invalid state to confirm payment."},
                                status=status.HTTP_400_BAD_REQUEST)

            # 4. transaction_step=3 (입금 완료)로 변경 후 저장
            exchange.transaction_step = 4
            exchange.save()
            print(f"[PaymentCompleteView] exchange updated: {exchange}")

            return Response({
                "detail": "Payment marked as completed.",
                "transaction_step": 4
            }, status=status.HTTP_200_OK)

        except Ticket.DoesNotExist:
            print(f"[PaymentCompleteView] Ticket with id={ticket_id} does not exist.")
            return Response({"detail": "ticket not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exchange.DoesNotExist:
            print(f"[PaymentCompleteView] exchange with ticket_id={ticket_id} does not exist.")
            return Response({"detail": "exchange not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            print(f"[PaymentCompleteView] An unexpected error occurred: {str(e)}")
            return Response({"detail": f"An error occurred: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConfirmReceiptView(APIView):

    @swagger_auto_schema(
        operation_id="입금 확인 및 거래 완료",
        operation_description="(transaction_step=3) → 판매자가 입금을 확인하면 transaction_step=4로 변경하고 거래 완료 처리합니다.",
        responses={
            200: "Receipt confirmed. Transfer completed.",
            400: "Invalid state.",
            403: "Invalid user or permission denied.",
            404: "exchange not found.",
            500: "서버 에러",
        }
    )
    def post(self, request, ticket_id):
        print(f"[ConfirmReceiptView] POST called with ticket_id: {ticket_id}")
        try:
            user = request.user
            print(f"[ConfirmReceiptView] Request user: {user}, is_authenticated: {user.is_authenticated}")

            # 1. Ticket 및 Exchange 찾기
            ticket = Ticket.objects.get(id=ticket_id)
            print(f"[ConfirmReceiptView] Ticket found: {ticket}")
            exchange = Exchange.objects.get(ticket_1=ticket)  # 혹은 ticket_2
            print(f"[ConfirmReceiptView] exchange found: {exchange}")

            # 2. 권한 체크(양도자만 가능)
            if user != exchange.owner:
                print(f"[ConfirmReceiptView] User {user} is not the owner")
                return Response({"detail": "Only the seller can confirm receipt."},
                                status=status.HTTP_403_FORBIDDEN)

            # 3. transaction_step이 3인지 확인
            if exchange.transaction_step != 4:
                print(f"[ConfirmReceiptView] Invalid state to confirm receipt: transaction_step={exchange.transaction_step}")
                return Response({"detail": "Invalid state to confirm receipt."},
                                status=status.HTTP_400_BAD_REQUEST)

            # 4. transaction_step=4 (거래 완료)로 변경 후 저장
            exchange.transaction_step = 5
            exchange.save()
            print(f"[ConfirmReceiptView] exchange updated: {exchange}")

            # (선택) Ticket 상태 업데이트
            #   - TransferIntentView 예시에서 ticket을 exchange.ticket 으로 접근했다면,
            #     모델 구조에 맞게 수정해야 합니다.
            #   - 필드명이 다를 수도 있으니 주의하세요.
            ticket.status_transfer = "transfer_completed"
            ticket.save()
            print(f"[ConfirmReceiptView] Ticket updated: {ticket}")

            # 판매자 전화번호(마스킹되지 않은) 뒷자리 등 필요한 정보 응답
            phone_last_digits = ticket.phone_last_digits
            print(f"[ConfirmReceiptView] Transferor profile: {phone_last_digits}")

            return Response({
                "detail": "Transfer completed.",
                "transaction_step": 4,
                "ticket_file_url": ticket.uploaded_file.url if ticket.uploaded_file else None,
                "phone_last_digits": phone_last_digits,
            }, status=status.HTTP_200_OK)

        except Ticket.DoesNotExist:
            print(f"[ConfirmReceiptView] Ticket with id={ticket_id} does not exist.")
            return Response({"detail": "ticket not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exchange.DoesNotExist:
            print(f"[ConfirmReceiptView] exchange with ticket_id={ticket_id} does not exist.")
            return Response({"detail": "exchange not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            print(f"[ConfirmReceiptView] An unexpected error occurred: {str(e)}")
            return Response({"detail": f"An error occurred: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LeaveExchangeView(APIView):

    @swagger_auto_schema(
        operation_id="대화방 나가기",
        operation_description="양수자가 대화방에서 나가면 새로운 사용자가 대화방에 참여할 수 있습니다. 양수자만 대화방에서 나갈 수 있습니다.",
        responses={
            200: "You have left the exchange. A new user can now join.",
            403: "You are not part of this exchange.",
            404: "exchange not found."
        }
    )
    def post(self, request, ticket_id):
        print(f"[LeaveexchangeView] POST called with exchange_id: {ticket_id}")
        try:
            user = request.user
            print(f"[LeaveexchangeView]Request user: {user}, is_authenticated: {user.is_authenticated}")
            ticket = Ticket.objects.get(id=ticket_id)
            print(f"[LeaveexchangeView] Ticket found: {ticket}")
            exchange = Exchange.objects.get(ticket=ticket)
            print(f"[LeaveexchangeView] exchange found: {exchange}")
            # Only the transferee can leave the exchange
            if exchange.transferee != user:
                print(f"[LeaveexchangeView] User {user} is not the transferee")
                return Response({"detail": "You are not part of this exchange."}, status=status.HTTP_403_FORBIDDEN)

            # Reset the transferee and transaction step
            ticket.transferee = None
            ticket.status_transfer = "waiting"
            ticket.save()
            # TicketPost 가져오기
            try:
                ticket_post = TicketPost.objects.get(ticket=ticket)  # `ticket_id`를 `ticket`으로 연결
            except TicketPost.DoesNotExist:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

            # TicketPost의 ticket 정보 동기화
            ticket_post.ticket = ticket
            ticket_post.save()
            
            exchange.transferee = None
            exchange.transaction_step = 0
            exchange.is_transfer_intent = False
            exchange.is_acceptance_intent = False
            exchange.save()
            print(f"[LeaveexchangeView] exchange updated after user left: {exchange}")

            return Response({"detail": "You have left the exchange. A new user can now join."}, status=status.HTTP_200_OK)

        except exchange.DoesNotExist:
            print(f"[LeaveexchangeView] exchange with id {ticket_id} does not exist.")
            return Response({"detail": "exchange not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"[LeaveexchangeView] An unexpected error occurred: {str(e)}")
            return Response({"detail": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


