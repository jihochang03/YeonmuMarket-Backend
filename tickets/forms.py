from django import forms
from .models import Ticket, TransferRequest

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['seat', 'booking_details', 'price', 'casting', 'file_upload']  # Include the file_upload field
        
    def clean_file_upload(self):
        file = self.cleaned_data.get('file_upload')
        if file and file.size > 10 * 1024 * 1024:  # Set a size limit, e.g., 10MB
            raise forms.ValidationError("File size exceeds 10MB")
        return file

class TransferRequestForm(forms.ModelForm):
    class Meta:
        model = TransferRequest
        fields = ['buyer_message']
