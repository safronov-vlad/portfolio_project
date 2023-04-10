# Generated by Django 3.2.7 on 2023-01-18 12:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_transaction'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegistrationRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=80, verbose_name='Логин')),
                ('password', models.CharField(max_length=80, verbose_name='Пароль')),
                ('email', models.CharField(max_length=80, verbose_name='email')),
                ('dt_create', models.DateTimeField(auto_now_add=True, verbose_name='Дата запроса')),
            ],
            options={
                'verbose_name': 'Заявка на регистрацию',
                'verbose_name_plural': 'Заявки на рагистрацию',
            },
        ),
        migrations.AlterModelOptions(
            name='transaction',
            options={'verbose_name': 'Транзакция', 'verbose_name_plural': 'Транзакции'},
        ),
        migrations.AlterField(
            model_name='transaction',
            name='desc',
            field=models.IntegerField(choices=[(1, 'Абонентская плата'), (2, 'Аренда сервера'), (3, '...'), (4, 'Пополнение баланса')], default=3, verbose_name='Описание'),
        ),
    ]
