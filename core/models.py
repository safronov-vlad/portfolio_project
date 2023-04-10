from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username, password, **extra_fields):
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, password, **extra_fields)


class Client(AbstractBaseUser, PermissionsMixin):
    # данные клиента
    username = models.CharField('Имя пользователя', max_length=200, unique=True)
    email = models.EmailField('Электронная почта', blank=True)
    phone = models.CharField('Телефон', max_length=200, null=True, blank=True)
    telegram = models.CharField('Телеграм', blank=True, max_length=100)
    first_name = models.CharField('Имя', blank=True, max_length=100)
    last_name = models.CharField('Фамилия', blank=True, max_length=100)
    # технические поля
    employer = models.ForeignKey('self', models.CASCADE, 'employees', null=True, blank=True, verbose_name='Главный аккаунт')
    balance = models.FloatField("Баланс", default=0)
    tariff = models.IntegerField("Стоимость тарифа", default=32)
    goip_mode = models.BooleanField("Работа через goip?", default=False)
    freeze = models.BooleanField("Замарожено?", default=False)
    our_server = models.BooleanField("Наш Сервер?", default=True)
    multi = models.BooleanField("Включить мульти аккаунт?", default=False)
    available_slots = models.ManyToManyField('Simbank', through='AvailableSmbSlots', related_name='client_slots')
    available_lines = models.ManyToManyField('Goip', through='AvailableLines', related_name='client_lines')
    # доп. поля
    reset_pass = models.BooleanField('Открыт сброс пароля', default=False)
    comment = models.TextField('Комментарий', null=True, blank=True)
    is_active = models.BooleanField('Активен?', default=False)
    is_tech_support = models.BooleanField('Тех подджержка', default=False)
    is_staff = models.BooleanField('Статус персонала', default=False)
    is_superuser = models.BooleanField('Статус суперпользователя', default=False)
    date_joined = models.DateTimeField('Дата регистрации', auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'

    def __str__(self):
        return '%s' % (self.username, )

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'


class SimbankScheduler(models.Model):
    class Meta:
        verbose_name = "Симбанк Scheduler"
        verbose_name_plural = "Симбанки Scheduler"

    name = models.CharField("Имя Scheduler", max_length=200)
    client = models.ForeignKey(Client, models.SET_NULL, verbose_name="Клиент", null=True)
    server = models.CharField("Путь, по которому доступен Scheduler", max_length=80)
    sc_login = models.CharField("Логин Scheduler", max_length=80, default='admin')
    sc_pass = models.CharField("Пароль Scheduler", max_length=80, default='admin')
    sms_login = models.CharField("Логин SmsServer", max_length=80, default='root')
    sms_pass = models.CharField("Пароль SmsServer", max_length=80, default='root')
    status = models.BooleanField("Работает?", default=False)
    rebooting = models.BooleanField("Перезагружается", default=False)
    install_progress = models.CharField('Статус установки', max_length=80, null=True, blank=True)
    clo_server = models.BooleanField('Сервер на CLO', default=False)
    ansible_server_id = models.IntegerField('ID сервера на Ansible Server', default=0)
    datetime = models.DateTimeField('Дата создания', auto_now_add=True)

    def __str__(self):
        return self.name

class Simbank(models.Model):
    class Meta:
        verbose_name = "Симбанк"
        verbose_name_plural = "Симбанки"
        unique_together = ['client', 'smb_id']
        
    TYPE_1 = 1
    TYPE_2 = 2
    
    TYPES = [
        (TYPE_1, '128'),
        (TYPE_2, '32')
    ]

    IMEI_1 = 1
    IMEI_2 = 2
    IMEI_3 = 3
    IMEI_4 = 4
    IMEI_5 = 5
    
    IMEI_TYPE = [
        (IMEI_1, 'GOIP Default'),
        (IMEI_2, 'Random'),
        (IMEI_3, 'Set with Slot'),
        (IMEI_4, 'Random with IMSI'),
        (IMEI_5, 'Set from database with IMSI')
    ]

    name = models.CharField("Имя симбанка", max_length=200)
    client = models.ForeignKey(Client, models.SET_NULL, verbose_name="Клиент", null=True)
    smb_id = models.IntegerField("ID симбанка")
    password = models.CharField("Пароль симбанка", max_length=200)
    smb_type = models.IntegerField("Тип симбанка", default=TYPE_1, choices=TYPES)
    imeimode = models.IntegerField("Прицнип формирования IMEI сим карты", default=IMEI_1, choices=IMEI_TYPE)
    count_active = models.IntegerField("Кол-во активных сим", default=0)
    status = models.BooleanField("Работает?", default=False)
    smb_server = models.ForeignKey(SimbankScheduler, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def get_slots(self): # noqa
        data = []
        for i in range(1, int(self.get_smb_type_display()) + 1, 1):
            prefix = 1000 if self.smb_type == 1 else 100
            data.append(str(i + self.smb_id * prefix))

        return data


class Goip(models.Model):
    class Meta:
        verbose_name = "GOIP Шлюз"
        verbose_name_plural = "GOIP Шлюзы"
        unique_together = ['client', 'goip_id']
        
    GOIP_TYPE_1 = 1
    GOIP_TYPE_2 = 2
    GOIP_TYPE_3 = 3
    GOIP_TYPE_4 = 4
    GOIP_TYPE_5 = 5

    GOIPTYPES = [
        (GOIP_TYPE_1, '1'),
        (GOIP_TYPE_2, '4'),
        (GOIP_TYPE_3, '8'),
        (GOIP_TYPE_4, '16'),
        (GOIP_TYPE_5, '32')
    ]

    name = models.CharField("Имя шлюза", max_length=200)
    client = models.ForeignKey(Client, models.SET_NULL, verbose_name="Клиент", null=True)
    goip_id = models.IntegerField("Id шлюза")
    password = models.CharField(max_length=200, verbose_name=u"Пароль шлюза для сервера")
    goip_type = models.IntegerField(default=GOIP_TYPE_3, choices=GOIPTYPES)
    smb_server = models.ForeignKey(SimbankScheduler, verbose_name=u"Scheduler", on_delete=models.CASCADE)
    status = models.BooleanField(default=False, verbose_name="Работает?")

    def __str__(self):
        return self.name


class Operator(models.Model):
    class Meta:
        verbose_name = "Провайдер связи"
        verbose_name_plural = "Провайдеры связи"

    name = models.CharField("Оператор", max_length=200)
    favicon = models.CharField("Изображение", max_length=200, default="https://favicon.yandex.net/favicon/")

    def __str__(self):
        return self.name


class Service(models.Model):
    class Meta:
        verbose_name = u"Сервис"
        verbose_name_plural = u"Сервисы"

    name = models.CharField("Название сервиса", max_length=200)
    url = models.CharField("Url сервиса", max_length=200)
    comment = models.CharField("Комментарий", max_length=200, null=True, blank=True)

    def __str__(self):
        return self.name


class Sim(models.Model):
    class Meta:
        verbose_name = "Сим-карта"
        verbose_name_plural = "Сим-Карты"
        unique_together = ['client', 'smb_slot']

    name = models.CharField("Номер симкарты", max_length=200)
    client = models.ForeignKey(Client, models.SET_NULL, verbose_name="Клиент", null=True)
    operator = models.ForeignKey(Operator, verbose_name="Оператор", on_delete=models.SET_NULL, null=True)
    balance = models.FloatField('Баланс', default=0)
    balance_dt = models.DateTimeField('Дата обновления баланса', auto_now=True)
    add_dt = models.DateField('Дата добавления в панель', auto_now_add=True)
    services = models.ManyToManyField(Service, verbose_name='Заюзаные сервисы', blank=True)
    smb = models.ForeignKey(Simbank, verbose_name='В каком банке вставлена', on_delete=models.CASCADE, null=True)
    pay_operation = models.BooleanField("Платные действия", default=False)
    last_pay_operation = models.DateTimeField('Дата последнего платного действия', null=True)
    status = models.BooleanField('Статус', default=True)
    smb_slot = models.IntegerField('Номер слота симбанка, в который вставлена Сим', null=True, blank=True)
    goip_id = models.CharField('Goip Slot', max_length=200, null=True, blank=True)
    imsi = models.CharField('IMSI', max_length=200, null=True, blank=True)
    imei = models.CharField('IMEI', max_length=200, null=True, blank=True)

    def __str__(self):
        return self.name


class AvailableLines(models.Model):
    class Meta:
        verbose_name = "Доступные юзеру GOIP линии"
        verbose_name_plural = "Доступные юзеру GOIP линии"
        unique_together = ['client', 'gateway']

    client = models.ForeignKey(Client, models.CASCADE, verbose_name="Клиент", related_name='available_gateway_lines')
    gateway = models.ForeignKey(Goip, models.CASCADE, verbose_name="Шлюз")
    lines = models.JSONField('Доступные линии', default=list)

    def __str__(self):
        return f'{self.client.username} - {self.gateway.name}'


class AvailableSmbSlots(models.Model):
    class Meta:
        verbose_name = "Доступные юзеру SMB слоты"
        verbose_name_plural = "Доступные юзеру SMB слоты"
        unique_together = ['client', 'smb']

    client = models.ForeignKey(Client, models.CASCADE, verbose_name="Клиент", related_name='available_smb_slots')
    smb = models.ForeignKey(Simbank, models.CASCADE, verbose_name="Симбанк")
    slots = models.JSONField('Доступные слоты', default=list)

    def __str__(self):
        return f'{self.client.username} - {self.smb.name}'


class Transaction(models.Model):
    class Meta:
        verbose_name = "Транзакция"
        verbose_name_plural = "Транзакции"
        ordering = ('-id',)

    TRANS_TYPE_1 = 1
    TRANS_TYPE_2 = 2
    TRANS_TYPE_3 = 3
    TRANS_TYPE_4 = 4

    TRANS_TYPES = [
        (TRANS_TYPE_1, 'Абонентская плата'),
        (TRANS_TYPE_2, 'Аренда сервера'),
        (TRANS_TYPE_3, '...'),
        (TRANS_TYPE_4, 'Пополнение баланса')
    ]

    client = models.ForeignKey(Client, models.SET_NULL, verbose_name="Клиент", null=True)
    type = models.BooleanField('Списание/Пополнение', default=False)
    desc = models.IntegerField('Описание', choices=TRANS_TYPES, default=TRANS_TYPE_3)
    bank_id = models.CharField('ID транзакции в банке', max_length=100, null=True, blank=True)
    value = models.FloatField('Сумма', default=0)
    dt_create = models.DateTimeField('Дата создания', auto_now_add=True)
    dt_update = models.DateTimeField('Дата последнего обновления', auto_now=True)

    def __str__(self):
        return f'{"Пополнение" if self.type else "Списание"} - {self.client.username} - {self.get_desc_display()} - {self.value}'


class BankRequest(models.Model):
    class Meta:
        verbose_name = "Запрос на оплату"
        verbose_name_plural = "Запросы на оплату"

    client = models.ForeignKey(Client, models.SET_NULL, verbose_name="Клиент", null=True)
    bank_id = models.CharField('ID транзакции в банке', max_length=100, null=True, blank=True)
    value = models.FloatField('Сумма платежа', default=0)
    payed = models.BooleanField('Оплачено', default=False)

    def __str__(self):
        return str(self.id)

class RegistrationRequest(models.Model):
    class Meta:
        verbose_name = "Заявка на регистрацию"
        verbose_name_plural = "Заявки на рагистрацию"

    username = models.CharField('Логин', max_length=80)
    password = models.CharField('Пароль', max_length=80)
    email = models.CharField('email', max_length=80)
    activated = models.BooleanField('Активирован', default=False)
    dt_create = models.DateTimeField('Дата запроса', auto_now_add=True)

    def __str__(self):
        return f'{self.username} - {self.email}'
