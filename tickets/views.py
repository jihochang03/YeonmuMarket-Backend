from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Ticket, TransferRequest, TransferRequest, TransferHistory
from .forms import TicketForm, TransferRequestForm
from .signals import notify_owner

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

def complete_transfer(request, transfer_id):
    # 양도 요청을 조회합니다.
    transfer_request = get_object_or_404(TransferRequest, id=transfer_id)
    
    if request.method == 'POST':
        # 양도 요청 완료 처리
        # 예: 양도 요청을 완료 상태로 변경하고 저장
        # 실제 구현은 여기에 추가합니다.
        TransferHistory.objects.create(
            ticket=transfer_request.ticket,
            transferee=transfer_request.buyer,
            transfer_date=transfer_request.created_at,
            chat_room="Completed chat room"
        )
        transfer_request.mark_as_completed()  # 양도 요청 완료 상태로 변경
        return redirect('home')  # 완료 후 홈으로 리디렉션

    return render(request, 'complete_transfer.html', {'transfer_request': transfer_request})
