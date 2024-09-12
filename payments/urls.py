from django.urls import path
from . import views

urlpatterns = [
    path('confirm/<int:payment_id>/', views.confirm_payment, name='confirm_payment'),
]
