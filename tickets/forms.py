from django import forms
from .models import Ticket, TransferRequest

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['seat', 'booking_details', 'price', 'casting']
        
class TransferRequestForm(forms.ModelForm):
    class Meta:
        model = TransferRequest
        fields = ['buyer_message']  # Ensure this matches the TransferRequest model