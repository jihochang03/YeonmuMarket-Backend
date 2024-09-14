from django.urls import path
from .views import add_bank_account, verify_bank_account

urlpatterns = [
    path('add/', add_bank_account, name='add_bank_account'),
    path('verify/<int:bank_account_id>/', verify_bank_account, name='verify_bank_account'),
]
