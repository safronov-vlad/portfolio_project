# Generated by Django 3.2.7 on 2023-01-16 09:46

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_simbankscheduler_rebooting'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.BooleanField(default=False, verbose_name='Списание/Пополнение')),
                ('desc', models.IntegerField(choices=[(1, 'Абонентская плата'), (2, 'Аренда сервера'), (3, '...')], default=3, verbose_name='Описание')),
                ('value', models.FloatField(default=0, verbose_name='Сумма')),
                ('dt_create', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('dt_update', models.DateTimeField(auto_now=True, verbose_name='Дата последнего обновления')),
                ('client', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Клиент')),
            ],
            options={
                'verbose_name': 'Транзакция',
                'verbose_name_plural': 'Транзакция',
            },
        ),
    ]
