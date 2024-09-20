from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from .models import Conversation, Message
from tickets.models import TransferRequest, Ticket
from .tasks import send_transfer_notification, verify_payment, update_ticket_transfer, notify_user_of_completion

@login_required
def start_conversation(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    conversation, created = Conversation.objects.get_or_create(ticket=ticket)

    if request.method == 'POST':
        message_content = request.POST.get('message')
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=message_content
        )
        return redirect('view_conversation', conversation_id=conversation.id)
    
    return render(request, 'conversations/start_conversation.html', {'ticket': ticket})

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
            # Notify transferee with the transferor's account number using Celery
            send_transfer_notification.delay(conversation.transferee.email, "The transferor has expressed intent to transfer the ticket.")

        elif 'acceptance_intent' in request.POST:
            # You can add additional logic here, like revealing the account number
            pass

    return redirect('view_conversation', conversation_id=conversation.id)

@login_required
def complete_transfer(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.method == 'POST':
        if 'confirm_payment' in request.POST:
            # Offload payment verification and ticket update to Celery
            verify_payment.delay(conversation.ticket.id)
            update_ticket_transfer.delay(conversation.id)

            # Notify transferee and transferor of completion
            notify_user_of_completion.delay(conversation.transferee.email, conversation.ticket.id)
            notify_user_of_completion.delay(conversation.transferor.email, conversation.ticket.id)

            return redirect('transaction_history')

    return render(request, 'complete_transfer.html', {'conversation': conversation})
