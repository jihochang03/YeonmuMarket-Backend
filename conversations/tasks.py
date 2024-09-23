from celery import shared_task
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from .models import Conversation
from tickets.models import TransferRequest

#이중에 사용할 task 골라서 사용할 예정. 

@shared_task
def send_transfer_notification(email, message):
    """Send email notification about the ticket transfer."""
    send_mail(
        'Ticket Transfer Update',
        message,
        'hoyaho03@naver.com',  # Replace with your actual from email
        [email],
        fail_silently=False,
    )

@shared_task
def update_ticket_transfer(conversation_id):
    """Update ticket transfer status and conversation completion."""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    transfer_request = get_object_or_404(TransferRequest, ticket=conversation.ticket, buyer=conversation.transferee)
    
    transfer_request.mark_as_completed()
    transfer_request.save()  # Save changes to the transfer request
    
    # Update the conversation status
    conversation.is_completed = True
    conversation.save()

@shared_task
def notify_user_of_completion(user_email, ticket_id):
    """Notify user that the ticket transfer is completed."""
    send_mail(
        'Ticket Transfer Completed',
        f'Your ticket (ID: {ticket_id}) has been transferred successfully.',
        'hoyaho03@naver.com',  # Replace with your actual from email
        [user_email],
        fail_silently=False,
    )
