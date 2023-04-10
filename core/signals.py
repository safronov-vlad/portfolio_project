from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from .models import Client, Simbank, Goip, SimbankScheduler, Transaction, BankRequest
from .equipment import create_gateway, create_smb, delete_smb, delete_gateway, delete_server
from .transactions import create_transaction, delete_transaction
from core.serializers import SimbankSchedulerSerializer


@receiver(post_save, sender=SimbankScheduler)
def update_server_sign(sender, instance=None, created=False, **kwargs):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(f"server_state_{instance.client.id}", {
        "type": "chat.message",
        "message": SimbankSchedulerSerializer(instance).data
    })


@receiver(post_delete, sender=SimbankScheduler)
def delete_clo_server(sender, instance=None, created=False, **kwargs):
    if instance.clo_server and instance.ansible_server_id:
        delete_server(instance)


@receiver(post_save, sender=Client)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


@receiver(post_save, sender=Simbank)
def create_smb_sign(sender, instance=None, created=False, **kwargs):
    if created:
        create_smb(instance)


@receiver(post_save, sender=Goip)
def create_gateway_sign(sender, instance=None, created=False, **kwargs):
    if created:
        create_gateway(instance)


@receiver(post_delete, sender=Simbank)
def delete_smb_sign(sender, instance=None, created=False, **kwargs):
    delete_smb(instance)


@receiver(post_delete, sender=Goip)
def delete_gateway_sign(sender, instance=None, created=False, **kwargs):
    delete_gateway(instance)


@receiver(post_save, sender=Transaction)
def create_transaction_sign(sender, instance=None, created=False, **kwargs):
    if created:
        create_transaction(instance)


@receiver(post_delete, sender=Transaction)
def delete_transaction_sign(sender, instance=None, created=False, **kwargs):
    delete_transaction(instance)


@receiver(post_save, sender=BankRequest)
def update_bank_request_sign(sender, instance=None, created=False, **kwargs):
    if instance.payed and not Transaction.objects.filter(bank_id=instance.bank_id).exists():
        Transaction.objects.create(
            client=instance.client,
            value=instance.value,
            type=True,
            bank_id=instance.bank_id,
            desc=Transaction.TRANS_TYPE_4
        )
