import os
import sys
import json
import telebot
from telebot import types

import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_project_.settings")
django.setup()

from django.conf import settings
from django.contrib.auth import authenticate

from support.models import Ticket, TicketMessage
from core.models import Client

bot = telebot.TeleBot(settings.SUPPORT_TG_BOT)


class TelegramHelper:
    def __init__(self, tg_bot):
        self.tickets_data = {}
        self.bot = tg_bot

    def handle_text_message(self, message):
        if message.text == 'Список обращений':
            self.get_ticket_list(message)
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row('Список обращений')
            self.bot.send_message(message.chat.id, 'Нет такой команды', reply_markup=markup)

    def get_ticket_list(self, message):
        markup = types.InlineKeyboardMarkup()
        for t in Ticket.objects.filter(resolved=False):
            markup.add(types.InlineKeyboardButton(
                f"#{t.id}, Пользователь: {t.client.username}, Тема: {t.name}",
                callback_data=f'get.{t.id}'
            ))
        self.bot.send_message(message.chat.id, 'Список заявок:', reply_markup=markup)

    def reply(self, message, cancel = False):
        if cancel:
            msg = 'Отправка отменена'
        else:
            msg = 'Сообщение отправлено!'
        if not cancel:
            TicketMessage.objects.create(message=message.text, is_admin=True, ticket_id=self.tickets_data[message.chat.id])
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Написать еще", callback_data=f'reply.{self.tickets_data[message.chat.id]}')
        )
        markup.add(
            types.InlineKeyboardButton("Обновить диалог", callback_data=f'get.{self.tickets_data[message.chat.id]}')
        )
        markup.add(types.InlineKeyboardButton("Ко всем заявкам", callback_data=f'all.0'))
        self.bot.send_message(message.chat.id, msg, reply_markup=markup)

    def authorize_user(self, message):
        if len(message.text.split(' ')) == 2:
            user: Client = authenticate(**json.loads('{"username": "%s", "password": "%s"}' % tuple(message.text.split(' '))))
            if user:
                user.telegram = message.from_user.id
                user.save()
                self.bot.send_message(message.chat.id, 'Вы успешно авторизировались')
                self.get_ticket_list(message)
                return
        send = self.bot.send_message(message.chat.id, 'Не правильный логин или пароль, попробуйте ещё раз')
        self.bot.register_next_step_handler(send, tg_helper.authorize_user)

    def callback_action(self, call):
        action, value  = call.data.split('.') # noqa
        # получить данные тикета
        if action == 'get':
            ticket = Ticket.objects.get(id=value)
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(f"Ответить", callback_data=f'reply.{ticket.id}'))
            markup.add(types.InlineKeyboardButton(f"Ко всем заявкам", callback_data=f'all.0'))
            msg = f'Заявка #{ticket.id}\n\nПользователь: {ticket.client.username}\nТема: {ticket.name}\nОписание: {ticket.message}\n'
            if TicketMessage.objects.filter(ticket_id=value).exists():
                msg += '\nПереписка с клиентом:\n'
                for m in TicketMessage.objects.filter(ticket_id=value):
                    msg += f'{"Тех. Поддержка" if m.is_admin else "Клиент"}: {m.message}\n'
            else:
                msg += '\nВ диалоге сообщений пока нету'
            self.bot.send_message(call.message.chat.id, msg, reply_markup=markup)
        # ответить на заявку
        elif action == 'reply':
            markup = types.InlineKeyboardMarkup()
            self.tickets_data[call.message.chat.id] = value
            markup.add(types.InlineKeyboardButton(f"Отменить", callback_data=f'cancel_step.{value}'))
            send = self.bot.send_message(call.message.chat.id, 'Введите сообщение:', reply_markup=markup)
            self.bot.register_next_step_handler(send, self.reply)
        # отменить step handler
        elif action == 'cancel_step':
            self.bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
            self.reply(call.message, True)
        # все заявки
        elif action == 'all':
            markup = types.InlineKeyboardMarkup()
            for t in Ticket.objects.filter(resolved=False):
                markup.add(types.InlineKeyboardButton(f"#{t.id}, Пользователь: {t.client.username}, Тема: {t.name}", callback_data=f'get.{t.id}'))
            bot.send_message(call.message.chat.id, 'Список заявок:', reply_markup=markup)
        self.bot.answer_callback_query(call.id)

@bot.message_handler(commands=['start'])
def start_message(message):
    if Client.objects.filter(telegram=message.from_user.id).exists():
        tg_helper.get_ticket_list(message)
    else:
        send = bot.send_message(message.chat.id, 'Вы не зарегистрированы, введите ваш логин и пароль (через пробел)')
        bot.register_next_step_handler(send, tg_helper.authorize_user)

@bot.message_handler(content_types=['text'])
def text_handler(message):
    if Client.objects.filter(telegram=message.from_user.id).exists():
        tg_helper.handle_text_message(message)
    else:
        send = bot.send_message(message.chat.id, 'Вы не зарегистрированы, введите ваш логин и пароль (через пробел)')
        bot.register_next_step_handler(send, tg_helper.authorize_user)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    tg_helper.callback_action(call)


tg_helper = TelegramHelper(bot)
bot.infinity_polling()
