# from datetime import datetime
from rest_framework import serializers
from .models import Ticket, TicketMessage


class TicketSerializer(serializers.ModelSerializer):
    def validate_client(self, data):
        return self.context['request'].user

    class Meta:
        model = Ticket
        fields = '__all__'


class TicketMessageSerializer(serializers.ModelSerializer):
    dt_create_str = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = TicketMessage
        fields = '__all__'

    def validate_client(self, data):
        return self.context['request'].user

    def get_dt_create_str(self, obj):
        return obj.dt_create.strftime('%d.%m.%Y %H:%M')
