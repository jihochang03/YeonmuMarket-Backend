from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from .models import Conversation, Message
from tickets.models import TransferRequest, Ticket

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
            # Notify transferee with the transferor's account number
            # This might be done through a notification system or email
            pass  # Implement notification logic here
    
        elif 'acceptance_intent' in request.POST:
            # Send transferor's account number to transferee
            # This could be displayed in the conversation view or sent via notification
            pass  # Implement logic to reveal account number here

    return redirect('conversation_view', ticket_id=conversation.ticket.id)

@login_required
def complete_transfer(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    if request.method == 'POST':
        if 'confirm_payment' in request.POST:
            conversation.is_completed = True
            conversation.save()

            # Update transferor and transferee's ticket lists
            transfer_request = TransferRequest.objects.get(ticket=conversation.ticket, buyer=conversation.transferee)
            transfer_request.mark_as_completed()
            
            return redirect('transaction_history')
    
    return render(request, 'complete_transfer.html', {'conversation': conversation})