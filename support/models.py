from django.db import models
from core.models import Client


class Ticket(models.Model):
    class Meta:
        verbose_name = "Тикет"
        verbose_name_plural = "Тикеты"
        ordering = ('-id',)

    name = models.CharField('Описание', max_length=200)
    message = models.TextField('Проблема')
    client = models.ForeignKey(Client, models.CASCADE, verbose_name='Клиент')
    resolved = models.BooleanField('Решено?', default=False)
    dt_create = models.DateTimeField('Дата создания', auto_now_add=True)

    def __str__(self):
        return f'{self.client.username} - {self.id}'


class TicketMessage(models.Model):
    class Meta:
        verbose_name = "Сообщение тикета"
        verbose_name_plural = "Сообщения тикетов"
        ordering = ('-id',)

    message = models.TextField('Сообщение')
    ticket = models.ForeignKey(Ticket, models.CASCADE)
    is_admin = models.BooleanField('Сообщение от администратора', default=False)
    dt_create = models.DateTimeField('Дата сообщения', auto_now_add=True)

    def __str__(self):
        return f'{self.id}'
