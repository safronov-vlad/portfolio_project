# Generated by Django 3.2.7 on 2023-03-08 10:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_auto_20230131_1714'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='reset_pass',
            field=models.BooleanField(default=False, verbose_name='Открыт сброс пароля'),
        ),
    ]