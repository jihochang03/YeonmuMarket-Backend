from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import BankAccount
from .forms import BankAccountForm, VerifyBankAccountForm
from .utils import verify_code
from user.models import UserProfile

@login_required
def register_bank_account(request):
    if request.method == 'POST':
        form = BankAccountForm(request.POST)
        if form.is_valid():
            bank_account = form.save(commit=False)
            bank_account.user = request.user
            bank_account.save()
            # Initiate verification process
            return redirect('verify_bank_account', bank_account_id=bank_account.id)
    else:
        form = BankAccountForm()
    return render(request, 'add_bank_account.html', {'form': form})

@login_required
def verify_bank_account(request, bank_account_id):
    bank_account = get_object_or_404(BankAccount, id=bank_account_id, user=request.user)
    
    if request.method == 'POST':
        form = VerifyBankAccountForm(request.POST)
        if form.is_valid():
            verification_code = form.cleaned_data['verification_code']
            if verify_code(bank_account, verification_code):
                # 인증 성공 처리
                bank_account.is_verified = True
                bank_account.save()
                
                # Update user profile with verified bank account
                user_profile, created = UserProfile.objects.get_or_create(user=request.user)
                user_profile.is_payment_verified = True
                user_profile.bank_account = bank_account
                user_profile.save()
                
                return redirect('payment_status', bank_account_id=bank_account.id)
            else:
                return render(request, 'verify_bank_account.html', {
                    'form': form, 
                    'error': '인증 코드가 올바르지 않습니다. 다시 시도해 주세요.'
                })
    else:
        form = VerifyBankAccountForm()
    
    return render(request, 'verify_bank_account.html', {'form': form})

def payment_status(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    return render(request, 'payments/payment_status.html', {'payment': payment})
