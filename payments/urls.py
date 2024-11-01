from django.urls import path
from .views import AccountRegisterView, AccountDetailView

urlpatterns = [
    path('register/', AccountRegisterView.as_view(), name='account-register'),
    path('', AccountDetailView.as_view(), name='account-detail'),
]