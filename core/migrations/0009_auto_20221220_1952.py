# Generated by Django 3.2.7 on 2022-12-20 19:52

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_client_employer'),
    ]

    operations = [
        migrations.CreateModel(
            name='AvailableSmbSlots',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slots', models.JSONField(default=list, verbose_name='Доступные слоты')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='available_smb_slots', to=settings.AUTH_USER_MODEL, verbose_name='Клиент')),
                ('smb', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.simbank', verbose_name='Симбанк')),
            ],
            options={
                'verbose_name': 'Доступные юзеру SMB слоты',
                'verbose_name_plural': 'Доступные юзеру SMB слоты',
                'unique_together': {('client', 'smb')},
            },
        ),
        migrations.CreateModel(
            name='AvailableLines',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lines', models.JSONField(default=list, verbose_name='Доступные линии')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='available_gateway_lines', to=settings.AUTH_USER_MODEL, verbose_name='Клиент')),
                ('gateway', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.goip', verbose_name='Шлюз')),
            ],
            options={
                'verbose_name': 'Доступные юзеру GOIP линии',
                'verbose_name_plural': 'Доступные юзеру GOIP линии',
                'unique_together': {('client', 'gateway')},
            },
        ),
        migrations.AddField(
            model_name='client',
            name='available_lines',
            field=models.ManyToManyField(related_name='client_lines', through='core.AvailableLines', to='core.Goip'),
        ),
        migrations.AddField(
            model_name='client',
            name='available_slots',
            field=models.ManyToManyField(related_name='client_slots', through='core.AvailableSmbSlots', to='core.Simbank'),
        ),
    ]
