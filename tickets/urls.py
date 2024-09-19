from django.urls import path
from .views import home, list_ticket, view_ticket, transfer_ticket, transaction_history, share_ticket, complete_transfer, transfer_history_detail, conversation_view, cancel_transfer

urlpatterns = [
    path('home/', home, name='home'),
    path('list/', list_ticket, name='list_ticket'),
    path('<int:ticket_id>/', view_ticket, name='view_ticket'),
    path('transfer/<int:request_id>/', transfer_ticket, name='transfer_ticket'),
    path('history/', transaction_history, name='transaction_history'),
    path('history/<int:id>/', transfer_history_detail, name='transfer_history_detail'),
    path('share/<int:ticket_id>/', share_ticket, name='share_ticket'),
    path('<int:ticket_id>/conversation/', conversation_view, name='conversation_view'),
    path('complete-transfer/<int:transfer_id>/', complete_transfer, name='complete_transfer'),
    path('cancel-transfer/<int:transfer_id>/', cancel_transfer, name='cancel_transfer'),
]
