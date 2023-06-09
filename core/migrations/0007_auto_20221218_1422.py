# Generated by Django 3.2.7 on 2022-12-18 14:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_auto_20221101_1358'),
    ]

    operations = [
        migrations.AlterField(
            model_name='goip',
            name='goip_type',
            field=models.IntegerField(choices=[(1, '1'), (2, '4'), (3, '8'), (4, '16'), (5, '32')], default=3),
        ),
        migrations.AlterField(
            model_name='sim',
            name='name',
            field=models.CharField(max_length=200, verbose_name='Номер симкарты'),
        ),
        migrations.AlterField(
            model_name='simbank',
            name='smb_type',
            field=models.IntegerField(choices=[(1, 'SMB128'), (2, 'SMB32')], default=1, verbose_name='Тип симбанка'),
        ),
    ]
