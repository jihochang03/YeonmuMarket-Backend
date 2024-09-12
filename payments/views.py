from django.shortcuts import render, get_object_or_404, redirect
from .models import Payment

def confirm_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.method == 'POST':
        # 여기서 실제 송금 확인 로직을 구현
        payment.status = 'completed'
        payment.save()
        # 알림 또는 후속 처리를 추가할 수 있음
        return redirect('payment_success')  # 성공 페이지로 리디렉션
    
    return render(request, 'payments/confirm_payment.html', {'payment': payment})
