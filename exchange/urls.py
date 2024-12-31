from django.urls import path
from .views import (
    JoinExchangeView, ExchangeDetailView, TransferIntentView,
    PaymentCompleteView, ConfirmReceiptView, LeaveExchangeView,
)
from .views import fetch_image

urlpatterns = [
    path('join/<int:ticket_id>/', JoinExchangeView.as_view(), name='join-exchange'),
    path('<int:ticket_id>/', ExchangeDetailView.as_view(), name='exchange-detail'),
    path('<int:ticket_id>/transfer-intent/', TransferIntentView.as_view(), name='transfer-intent'),
    path('<int:ticket_id>/payment-complete/', PaymentCompleteView.as_view(), name='payment-complete'),
    path('<int:ticket_id>/confirm-receipt/', ConfirmReceiptView.as_view(), name='confirm-receipt'),
    path('<int:ticket_id>/leave/', LeaveExchangeView.as_view(), name='leave-conversation'),
    path('fetch_image', fetch_image, name='fetch_image'),
]
