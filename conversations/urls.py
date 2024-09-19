from django.urls import path
from . import views

urlpatterns = [
    path('start/<int:ticket_id>/', views.start_conversation, name='start_conversation'),
    path('<int:conversation_id>/', views.view_conversation, name='view_conversation'),
    path('<int:conversation_id>/intent-to-transfer/', views.intent_to_transfer, name='intent_to_transfer'),
    path('<int:conversation_id>/complete-transfer/', views.complete_transfer, name='complete_transfer'),
]