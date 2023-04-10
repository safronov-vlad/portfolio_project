# Generated by Django 3.2.7 on 2022-12-27 11:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_auto_20221220_1952'),
    ]

    operations = [
        migrations.AddField(
            model_name='simbankscheduler',
            name='clo_server',
            field=models.BooleanField(default=False, verbose_name='Сервер на CLO'),
        ),
        migrations.AlterField(
            model_name='simbank',
            name='smb_type',
            field=models.IntegerField(choices=[(1, '128'), (2, '32')], default=1, verbose_name='Тип симбанка'),
        ),
    ]
