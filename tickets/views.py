from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Ticket, TransferRequest, TransferHistory
from .forms import TicketForm, TransferRequestForm
from .signals import notify_owner
from conversations.models import Conversation, Message

# Ticket List View
class TicketListView(LoginRequiredMixin, ListView):
    model = Ticket
    template_name = "tickets/list_tickets.html"
    context_object_name = "tickets"

    def get_queryset(self):
        return Ticket.objects.filter(owner=self.request.user)

# Ticket Detail View
class TicketDetailView(LoginRequiredMixin, DetailView):
    model = Ticket
    template_name = "tickets/view_ticket.html"
    context_object_name = "ticket"

# Create a new ticket
class TicketCreateView(LoginRequiredMixin, CreateView):
    model = Ticket
    form_class = TicketForm
    template_name = "tickets/transfer_ticket.html"
    success_url = reverse_lazy("tickets:list_tickets")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

# Update a ticket
class TicketUpdateView(LoginRequiredMixin, UpdateView):
    model = Ticket
    form_class = TicketForm
    template_name = "tickets/update_ticket.html"
    success_url = reverse_lazy("tickets:list_tickets")

# Delete a ticket
class TicketDeleteView(LoginRequiredMixin, DeleteView):
    model = Ticket
    template_name = "tickets/delete_ticket.html"
    success_url = reverse_lazy("tickets:list_tickets")

# Handle transfer request creation
class TransferRequestCreateView(LoginRequiredMixin, CreateView):
    model = TransferRequest
    form_class = TransferRequestForm
    template_name = "tickets/request_transfer.html"
    success_url = reverse_lazy("tickets:transfer_history")

    def form_valid(self, form):
        form.instance.requestor = self.request.user
        ticket = form.cleaned_data['ticket']
        notify_owner.send(sender=self.__class__, ticket=ticket, requestor=self.request.user)
        return super().form_valid(form)

# View transfer history
class TransferHistoryView(LoginRequiredMixin, ListView):
    model = TransferHistory
    template_name = "tickets/transfer_history.html"
    context_object_name = "transfer_histories"

    def get_queryset(self):
        return TransferHistory.objects.filter(owner=self.request.user)
