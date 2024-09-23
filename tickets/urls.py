from django.urls import path
from .views import (
    TicketListView, 
    TicketDetailView, 
    TransferListView,
    ReceivedListView
)

app_name = 'tickets'

urlpatterns = [
    path('', TicketListView.as_view()),
    path('<int:pk>/', TicketDetailView.as_view()),
    path('transferred/', TransferListView.as_view(), name='transferred-tickets'),
    path('received/', ReceivedListView.as_view(), name='received-tickets'),
]
