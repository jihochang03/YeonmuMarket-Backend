from django.urls import path
from .views import (
    TicketListCreateAPIView, 
    TicketRetrieveUpdateDestroyAPIView, 
    TransferRequestCreateAPIView, 
    TransferHistoryListAPIView
)

app_name = 'tickets'

urlpatterns = [
    path('tickets/', TicketListCreateAPIView.as_view(), name='ticket-list-create'),
    path('tickets/<int:pk>/', TicketRetrieveUpdateDestroyAPIView.as_view(), name='ticket-detail'),
    path('transfer-requests/', TransferRequestCreateAPIView.as_view(), name='transfer-request-create'),
    path('transfer-history/', TransferHistoryListAPIView.as_view(), name='transfer-history-list'),
]
