from django.urls import path
from .views import TicketListView, TicketDetailView, TicketCreateView, TicketUpdateView, TicketDeleteView, TransferRequestCreateView, TransferHistoryView

app_name = 'tickets'

urlpatterns = [
    path('', TicketListView.as_view(), name='list_tickets'),
    path('view/<int:pk>/', TicketDetailView.as_view(), name='view_ticket'),
    path('create/', TicketCreateView.as_view(), name='transfer_ticket'),
    path('update/<int:pk>/', TicketUpdateView.as_view(), name='update_ticket'),
    path('delete/<int:pk>/', TicketDeleteView.as_view(), name='delete_ticket'),
    path('transfer/request/', TransferRequestCreateView.as_view(), name='request_transfer'),
    path('transfer/history/', TransferHistoryView.as_view(), name='transfer_history'),
]
