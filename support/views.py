import django_filters
from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework.decorators import action

from .serializers import TicketSerializer, TicketMessageSerializer
from .models import Ticket, TicketMessage


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Ticket.objects.filter(client=self.request.user)


class TicketMessageFilter(filters.FilterSet):
    ticket = django_filters.CharFilter(field_name="ticket_id")

    class Meta:
        model = TicketMessage
        fields = ['ticket']


class TicketMessageViewSet(viewsets.ModelViewSet):
    serializer_class = TicketMessageSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.DjangoFilterBackend, SearchFilter)
    filterset_class = TicketMessageFilter

    def get_queryset(self):
        return TicketMessage.objects.select_related('ticket').filter(ticket__client=self.request.user)
