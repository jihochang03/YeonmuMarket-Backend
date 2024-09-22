from rest_framework import status 
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from .models import Conversation, Message
from tickets.models import Ticket
from user.models import UserProfile
from django.http import HttpResponseForbidden
from .kakao import send_kakao_message  # 카카오 메시지 전송 함수
from .point_utils import deduct_points, add_points  # 포인트 유틸리티 함수 import

@login_required
def start_conversation(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    conversation = Conversation.objects.filter(ticket=ticket, is_active=True).first()
    if conversation:
        return HttpResponseForbidden("이 티켓은 이미 다른 사용자와 대화 중입니다.")

    if request.method == 'POST':
        message_content = request.POST.get('message')
        conversation, created = Conversation.objects.get_or_create(ticket=ticket, transferee=request.user)
        conversation.transferor = ticket.owner
        conversation.is_active = True
        conversation.save()

        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=message_content
        )

        send_kakao_message(conversation.transferor, f"{request.user.username}님이 티켓 {ticket.title}에 대한 대화를 시작했습니다.")
        return redirect('view_conversation', conversation_id=conversation.id)
    
    return render(request, 'conversations/start_conversation.html', {'ticket': ticket, 'show_ticket_info': True})

@login_required
def view_conversation(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    messages = conversation.messages.all()

    if request.method == 'POST':
        message_content = request.POST.get('message')
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=message_content
        )
        return redirect('view_conversation', conversation_id=conversation.id)

    return render(request, 'conversations/view_conversation.html', {'conversation': conversation, 'messages': messages})

@login_required
def intent_to_transfer(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.method == 'POST':
        if 'transfer_intent' in request.POST:
            conversation.transfer_intent = True
            conversation.save()
        elif 'acceptance_intent' in request.POST:
            conversation.acceptance_intent = True
            conversation.save()

        if conversation.transfer_intent and conversation.acceptance_intent:
            return redirect('complete_transfer', conversation_id=conversation.id)

    return redirect('view_conversation', conversation_id=conversation.id)

@login_required
def complete_transfer(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if conversation.transfer_intent and conversation.acceptance_intent:
        ticket_price = conversation.ticket.price
        transferee_profile = conversation.transferee.userprofile
        transferor_profile = conversation.transferor.userprofile

        if transferee_profile.remaining_points < ticket_price:
            return HttpResponseForbidden("포인트가 부족하여 티켓 양도를 완료할 수 없습니다.")

        conversation.is_completed = True
        conversation.is_active = False
        conversation.save()

        # 포인트 차감 및 추가
        deduct_response = deduct_points(transferee_profile, ticket_price)
        if deduct_response.status_code != status.HTTP_200_OK:
            return deduct_response  # 차감 실패 시 응답 반환

        add_response = add_points(transferor_profile, ticket_price)
        if add_response.status_code != status.HTTP_200_OK:
            return add_response  # 추가 실패 시 응답 반환

        try:
            send_kakao_message(conversation.transferor, f"티켓 {conversation.ticket.title} 양도가 완료되었습니다.")
            send_kakao_message(conversation.transferee, f"티켓 {conversation.ticket.title} 양수가 완료되었습니다.")
        except Exception as e:
            print(f"카카오 메시지 전송 실패: {e}")
            return HttpResponseForbidden("양도는 완료되었으나 카카오 알림 전송에 실패했습니다.")

        return redirect('transaction_history')
    else:
        return HttpResponseForbidden("양도 및 양수 의사가 모두 확인되지 않았습니다.")
