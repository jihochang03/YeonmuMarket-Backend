from django.urls import path
from .views import (
    TicketPostListView, 
    TicketPostDetailView, 
    TransferListView,
    ReceivedListView
)
from .views import process_image

app_name = 'tickets'

urlpatterns = [
    path('create/', TicketPostListView.as_view()),
    path('ticketpost/<int:ticket_post_id>/', TicketPostDetailView.as_view()),
    path('transferred/', TransferListView.as_view(), name='transferred-tickets'),
    path('purchased/', ReceivedListView.as_view(), name='received-tickets'),
    path('process_image/', process_image, name='process_image'),
]
