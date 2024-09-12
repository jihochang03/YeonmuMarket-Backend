from django.shortcuts import get_object_or_404, render, redirect
from .models import Conversation, Message
from tickets.models import Ticket

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
    
    return render(request, 'conservations/start_conversation.html', {'ticket': ticket})

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
    
    return render(request, 'conservations/view_conversation.html', {'conversation': conversation, 'messages': messages})
