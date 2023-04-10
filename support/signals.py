import telebot
from telebot import types
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Ticket, TicketMessage
from core.models import Client

bot = telebot.TeleBot(settings.SUPPORT_TG_BOT)


@receiver(post_save, sender=Ticket)
def create_ticket(sender, instance=None, created=False, **kwargs):
    if created:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(
            f"#{instance.id}, Пользователь: {instance.client.username}, Тема: {instance.name}",
            callback_data=f'get.{instance.id}'
        ))
        for c in Client.objects.filter(is_tech_support=True, telegram__isnull=False):
            bot.send_message(c.telegram, f'Новая заявка #{instance.id}', reply_markup=markup)


@receiver(post_save, sender=TicketMessage)
def create_ticket_message(sender, instance=None, created=False, **kwargs):
    if created and not instance.is_admin:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(
            f"#{instance.ticket.id}, Пользователь: {instance.ticket.client.username}, Тема: {instance.ticket.name}",
            callback_data=f'get.{instance.ticket.id}'
        ))
        for c in Client.objects.filter(is_tech_support=True, telegram__isnull=False):
            bot.send_message(c.telegram, f'Новое сообщение в заявке #{instance.ticket.id}', reply_markup=markup)
