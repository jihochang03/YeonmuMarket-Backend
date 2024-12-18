from django.urls import path
from .views import (
    JoinConversationView, ConversationDetailView, TransferIntentView,
    PaymentCompleteView, ConfirmReceiptView, LeaveConversationView, TestPushNotificationView
)
from .views import fetch_image

urlpatterns = [
    path('join/<int:ticket_id>/', JoinConversationView.as_view(), name='join-conversation'),
    path('<int:ticket_id>/', ConversationDetailView.as_view(), name='conversation-detail'),
    path('<int:ticket_id>/transfer-intent/', TransferIntentView.as_view(), name='transfer-intent'),
    path('<int:ticket_id>/payment-complete/', PaymentCompleteView.as_view(), name='payment-complete'),
    path('<int:ticket_id>/confirm-receipt/', ConfirmReceiptView.as_view(), name='confirm-receipt'),
    path('<int:ticket_id>/leave/', LeaveConversationView.as_view(), name='leave-conversation'),
    path('fetch_image', fetch_image, name='fetch_image'),
    path('test/push-notification', TestPushNotificationView.as_view(), name='test-push-notification')
]
