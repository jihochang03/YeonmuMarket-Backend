from django.urls import path
from .views import register_bank_account, verify_bank_account, payment_status

urlpatterns = [
    path('register/', register_bank_account, name='register_bank_account'),
    path('verify/<int:bank_account_id>/', verify_bank_account, name='verify_bank_account'),
    path('payment-status/<int:bank_account_id>/', payment_status, name='payment_status'),
]
