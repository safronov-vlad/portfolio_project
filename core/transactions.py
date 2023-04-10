from django.db.models import F
from .models import Transaction, Client


def create_transaction(obj: Transaction) -> None:
    client: Client = obj.client
    client.balance = F('balance') - (-obj.value if obj.type else obj.value)
    client.save()


def delete_transaction(obj: Transaction) -> None:
    client: Client = obj.client
    client.balance = F('balance') + (-obj.value if obj.type else obj.value)
    client.save()
