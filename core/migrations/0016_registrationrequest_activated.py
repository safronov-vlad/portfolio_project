# Generated by Django 3.2.7 on 2023-01-18 13:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_auto_20230118_1251'),
    ]

    operations = [
        migrations.AddField(
            model_name='registrationrequest',
            name='activated',
            field=models.BooleanField(default=False, verbose_name='Активирован'),
        ),
    ]
