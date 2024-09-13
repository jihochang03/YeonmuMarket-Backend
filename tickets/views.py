from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Ticket, TransferRequest, TransferHistory
from .forms import TicketForm, TransferRequestForm
from .signals import notify_owner
from conversations.models import Conversation, Message

def home(request):
    return render(request, 'home.html')

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
    return render(request, 'tickets/list_tickets.html', {'form': form})

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
            return render(request, 'tickets/transfer_ticket.html', {'request': transfer_request, 'error': 'Payment verification failed'})
        
    return render(request, 'tickets/transfer_ticket.html', {'request': transfer_request})

def transaction_history(request):
    # 사용자가 양도한 티켓 내역을 모두 가져옵니다.
    transfer_histories = TransferHistory.objects.all()
    data = list(transfer_histories.values(
        'id',
        'ticket',
        'transferee',
        'transfer_date',
        'chat_room'
    ))
    return JsonResponse(data, safe=False)

def transfer_history_detail(request, id):
    # 특정 양도 내역을 가져옵니다.
    transfer_history = get_object_or_404(TransferHistory, id=id)
    data = {
        'id': transfer_history.id,
        'ticket': transfer_history.ticket.id,
        'transferee': transfer_history.transferee.id,
        'transfer_date': transfer_history.transfer_date.isoformat(),
        'chat_room': transfer_history.chat_room,
    }
    return JsonResponse(data)

def share_ticket(request, ticket_id):
    # 티켓을 조회합니다.
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if request.method == 'POST':
        # 티켓 공유 요청 처리
        # 예: 공유 대상 사용자에게 티켓 정보를 전송하거나 저장
        # 실제 구현은 여기에 추가합니다.
        return redirect('home')  # 완료 후 홈으로 리디렉션

    return render(request, 'share_ticket.html', {'ticket': ticket})

@login_required
def conversation_view(request, ticket_id):
    # Get the conversation for the ticket or create one
    ticket = get_object_or_404(Ticket, id=ticket_id)
    conversation, created = Conversation.objects.get_or_create(
        ticket=ticket,
        defaults={
            'transferor': ticket.owner,
            'transferee': request.user  # Assuming the user viewing is the transferee
        }
    )

    if request.method == "POST":
        # User sends a message
        content = request.POST.get('content')
        if content:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )

    messages = conversation.messages.all()
    return render(request, 'conversation.html', {'conversation': conversation, 'messages': messages})

@login_required
def complete_transfer(request, transfer_id):
    # Mark the transfer as completed
    conversation = get_object_or_404(Conversation, id=transfer_id)
    if request.method == "POST":
        conversation.is_completed = True
        conversation.save()
        # Update transferor and transferee's lists
        # Add logic to update the ticket status if needed
        return redirect('transaction_history')

    return render(request, 'complete_transfer.html', {'conversation': conversation})

@login_required
def cancel_transfer(request, transfer_id):
    # Mark the transfer as canceled
    conversation = get_object_or_404(Conversation, id=transfer_id)
    if request.method == "POST":
        # You can either delete the conversation or mark it as not completed
        conversation.is_completed = False
        conversation.save()
        return redirect('list_ticket')

    return render(request, 'cancel_transfer.html', {'conversation': conversation})
