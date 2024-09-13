from django.urls import path
from . import views

urlpatterns = [
    path('start/<int:ticket_id>/', views.start_conversation, name='start_conversation'),
    path('view/<int:conversation_id>/', views.view_conversation, name='view_conversation'),
]
