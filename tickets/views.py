from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Ticket, TransferRequest, TransferHistory
from .forms import TicketForm, TransferRequestForm
from .signals import notify_owner
from conversations.models import Conversation, Message

#홈 api
def home(request):
    return render(request, 'home.html')

#티켓 목록-양도와 양수를 분리
@login_required
def list_ticket(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.owner = request.user
            ticket.save()
            return redirect('home')
    else:
        form = TicketForm()

    # Fetch transferable tickets (owned by the user)
    transferable_tickets = Ticket.objects.filter(owner=request.user)

    # Fetch transfer requests where the user is the buyer
    my_transfer_requests = TransferRequest.objects.filter(buyer=request.user)

    return render(request, 'tickets/list_tickets.html', {
        'form': form,
        'transferable_tickets': transferable_tickets,
        'my_transfer_requests': my_transfer_requests,
    })

#특정 티켓을 보여주는 api
@login_required
def view_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if ticket.owner == request.user:
        return redirect('home')
    
    if request.method == 'POST':
        form = TransferRequestForm(request.POST)
        if form.is_valid():
            transfer_request = form.save(commit=False)
            transfer_request.ticket = ticket
            transfer_request.buyer = request.user
            transfer_request.save()
            notify_owner(transfer_request)
            return redirect('home')
    else:
        form = TransferRequestForm()

    return render(request, 'tickets/view_ticket.html', {'ticket': ticket, 'form': form})

# 여기서부터는 손봐야될듯.....

@login_required
def transfer_ticket(request, request_id):
    transfer_request = get_object_or_404(TransferRequest, id=request_id)
    
    if transfer_request.ticket.owner != request.user:
        return redirect('home')
    
    if request.method == 'POST':
        if transfer_request.payment_verified():
            transfer_request.mark_as_completed()
            return redirect('transfer_success')
        else:
            return render(request, 'tickets/transfer.html', {'request': transfer_request, 'error': 'Payment verification failed'})
        
    return render(request, 'tickets/transfer.html', {'request': transfer_request})

def transaction_history(request):
    transfer_histories = TransferHistory.objects.all()
    data = list(transfer_histories.values(
        'id',
        'ticket',
        'transferee',
        'transfer_date',
        'conversation'
    ))
    return JsonResponse(data, safe=False)

def transfer_history_detail(request, id):
    transfer_history = get_object_or_404(TransferHistory, id=id)
    data = {
        'id': transfer_history.id,
        'ticket': transfer_history.ticket.id,
        'transferee': transfer_history.transferee.id,
        'transfer_date': transfer_history.transfer_date.isoformat(),
        'conversation': transfer_history.conversation.id,
    }
    return JsonResponse(data)

@login_required
def share_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if request.method == 'POST':
        # Implement ticket sharing logic
        return redirect('home')

    return render(request, 'tickets/share_ticket.html', {'ticket': ticket})

@login_required
def conversation_view(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    conversation, created = Conversation.objects.get_or_create(
        ticket=ticket,
        defaults={
            'transferor': ticket.owner,
            'transferee': request.user
        }
    )

    if request.method == "POST":
        content = request.POST.get('content')
        if content:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )

    messages = conversation.messages.all()
    return render(request, 'conversations/conversation.html', {'conversation': conversation, 'messages': messages})

@login_required
def complete_transfer(request, transfer_id):
    transfer_history = get_object_or_404(TransferHistory, id=transfer_id)
    if request.method == "POST":
        transfer_history.conversation.is_completed = True
        transfer_history.conversation.save()
        return redirect('transaction_history')

    return render(request, 'tickets/complete_transfer.html', {'transfer_history': transfer_history})

@login_required
def cancel_transfer(request, transfer_id):
    transfer_history = get_object_or_404(TransferHistory, id=transfer_id)
    if request.method == "POST":
        transfer_history.conversation.is_completed = False
        transfer_history.conversation.save()
        return redirect('list_ticket')

    return render(request, 'tickets/cancel_transfer.html', {'transfer_history': transfer_history})
