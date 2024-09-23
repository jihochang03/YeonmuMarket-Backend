from django.urls import path
from .views import JoinConversationView, TransferIntentView, LeaveConversationView

urlpatterns = [
    path('join/<int:ticket_id>/', JoinConversationView.as_view(), name='join-conversation'),
    path('leave/<int:conversation_id>/', LeaveConversationView.as_view(), name='leave-conversation'),
    path('<int:conversation_id>/intent/', TransferIntentView.as_view()),
]