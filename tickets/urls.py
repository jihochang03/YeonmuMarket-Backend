from django.urls import path
from .views import home, list_ticket, view_ticket, transfer_ticket, transaction_history, share_ticket, complete_transfer, transfer_history_detail, conversation_view, cancel_transfer

urlpatterns = [
    path('', home, name='home'),
    path('list/', list_ticket, name='list_ticket'),
    path('ticket/<int:ticket_id>/', view_ticket, name='view_ticket'),
    path('transfer/<int:request_id>/', transfer_ticket, name='transfer_ticket'),
    path('history/', transaction_history, name='transaction_history'),
    path('share/<int:ticket_id>/', share_ticket, name='share_ticket'),
    path('conversation/<int:ticket_id>/', conversation_view, name='conversation'),
    path('complete/<int:transfer_id>/', complete_transfer, name='complete_transfer'),
    path('cancel/<int:transfer_id>/', cancel_transfer, name='cancel_transfer'),
    path('transfer_history/<int:id>/', transfer_history_detail, name='transfer_history_detail'),
]
