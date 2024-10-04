from django.urls import path
from .views import AccountRegisterView, AccountDetailView, AccountAddView

urlpatterns = [
    path('register/', AccountRegisterView.as_view(), name='account-register'),
    path('', AccountDetailView.as_view(), name='account-detail'),
    path('add-delete/', AccountAddView.as_view(), name='account-add-delete')
]