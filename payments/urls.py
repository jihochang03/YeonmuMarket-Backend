from django.urls import path
from .views import AccountRegisterView, AccountVerifyView, AccountDetailView, AccountRegisterAndVerifyView, AccountVerifyAndDeleteOldView

urlpatterns = [
    path('register/', AccountRegisterView.as_view(), name='account-register'),
    path('<int:account_id>/verify/', AccountVerifyView.as_view(), name='account-verify'),
    path('', AccountDetailView.as_view(), name='account-detail'),
    path('register-and-verify/', AccountRegisterAndVerifyView.as_view(), name='account-register-and-verify'),
    path('<int:account_id>/verify-and-delete/', AccountVerifyAndDeleteOldView.as_view(), name='account-verify-and-delete'),
]
