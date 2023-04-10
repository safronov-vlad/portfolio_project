import base64
import requests
from hashids import Hashids
from datetime import datetime
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate
from django.conf import settings as django_settings

from rest_framework import viewsets, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token

from .permissions import CheckPermissions

from .models import Client, SimbankScheduler, Simbank, Sim, Operator, Goip, Transaction, RegistrationRequest, BankRequest
from .serializers import (
    ClientSerializer,
    GoipSerializer,
    OperatorSerializer,
    SimSerializer,
    SimbankSchedulerSerializer,
    SimbankSerializer,
    EmployeeSerializer,
    TransactionSerializer, BankRequestSerializer
)
from .equipment import (
    get_gateway_slots,
    extend_gateway_item_with_operator_info,
    fill_sim_from_smb,
    get_all_sms,
    get_all_call,
    activate_sim,
    send_ussd,
    send_sms,
    update_shared_items,
    create_clo_server,
    reboot_clo_server
)
from .schemas import ResponseSchema, AuthorizationSchema
from .authentication import UserVar
from .utils import send_email


class AuthorizeAPIView(views.APIView):
    permission_classes = (AllowAny,)
    serializer_class = ClientSerializer
    strict_actions = []

    def post(self, request): # noqa
        user: Client = authenticate(**AuthorizationSchema(**request.data).dict())
        if user:
            # если есть главный акк
            if user.employer:
                if user.employer.balance > -1:
                    token_instance = Token.objects.get(user=user)
                    return Response(ResponseSchema(data={'token': token_instance.key, 'user_id': user.id}).dict())
            else:
                if user.balance > -1:
                    token_instance = Token.objects.get(user=user)
                    return Response(ResponseSchema(data={'token': token_instance.key, 'user_id': user.id}).dict())
            return Response(ResponseSchema(response_message='Пополните баланс').dict(), status=400)
        return Response(ResponseSchema(response_message='Неверные логин или пароль').dict(), status=400)


class ResetPasswordAPIView(views.APIView):
    permission_classes = (AllowAny,)
    serializer_class = ClientSerializer
    strict_actions = []

    def post(self, request): # noqa
        if request.data.get('email') and Client.objects.filter(email=request.data.get('email')).exists():
            client = Client.objects.get(email=request.data.get('email'))
            reset_hash = base64.b64encode(bytes(f"{client.id},{Client.objects.first().date_joined.strftime('%d-%m-%Y %H:%M:%S.%f')}", "utf-8")).decode()
            client.reset_pass = True
            client.save()
            send_email(
                request.data['email'],
                f'Сброс пароля от аккаунта {client.username} на сайте app.simbank.pro',
                {'username': client.username, 'email_verify': f'//{request.get_host()}/reset-password/?token={reset_hash}'}
            )

        return Response(ResponseSchema(response_message='Пользователя с таким e-mail адресом не существует').dict(), status=400)

    def get(self, request): # noqa
        if request.get('token'):
            token_data = base64.b64decode(request.GET.get("token")).decode().split(',')
            dt = datetime.strptime(token_data[1], '%d-%m-%Y %H:%M:%S.%f')
            client = Client.objects.filter(
                id=token_data[0],
                date_joined__year=dt.year,
                date_joined__month=dt.month,
                date_joined__day=dt.day,
                date_joined__hour=dt.hour,
                date_joined__minute=dt.minute,
                date_joined__second=dt.second,
            )
            if client:
                password = Hashids(min_length=10).encode(int(datetime.now().timestamp()))
                client.first().set_password(password)
                client.save()
                send_email(
                    request.data['email'],
                    f'Сброс пароля от аккаунта {client.username} на сайте app.simbank.pro',
                    {'username': client.username, 'new_password': password},
                    'email_reset_pass.html'
                )
                return HttpResponseRedirect(redirect_to=f'{django_settings.APPLICATION_FRONT_URL}/success-recovery-password')
        return HttpResponseRedirect(redirect_to=f'{django_settings.APPLICATION_FRONT_URL}/fail-recovery-password')


class RegistrationAPIView(views.APIView):
    permission_classes = (AllowAny,)
    serializer_class = ClientSerializer
    strict_actions = []

    def post(self, request): # noqa
        username = request.data.get('username')
        if username and not Client.objects.filter(username=username).exists() and not Client.objects.filter(email=request.data['email']):
            reg_obj = RegistrationRequest.objects.create(username=username, password=request.data['password'], email=request.data['email'])
            reg_hash = base64.b64encode(bytes(f"{reg_obj.id},{reg_obj.dt_create}", "utf-8")).decode()
            send_email(
                request.data['email'],
                'Подверждение регистрации на сайте app.simbank.pro',
                {'username': username, 'email_verify': f'//{request.get_host()}/email-verify/?token={reg_hash}'},
                'email_register.html'
            )
            return Response(ResponseSchema(response_message='Вы успешного зарегистрировались!<br>Вам на почту отправлено письмо с подтверждением!').dict())
        return Response(ResponseSchema(response_message='Пользователь с таким именем или почтой уже существует').dict(), status=400)


class VerifyRegistrationAPIView(views.APIView):
    permission_classes = (AllowAny,)
    serializer_class = ClientSerializer
    strict_actions = []

    def get(self, request): # noqa
        if request.GET.get('token'):
            token_data = base64.b64decode(request.GET.get("token")).decode().split(',')
            if len(token_data) == 2 and RegistrationRequest.objects.filter(id=token_data[0], dt_create=token_data[1], activated=False).exists():
                obj = RegistrationRequest.objects.get(id=token_data[0], dt_create=token_data[1], activated=False)
                if not Client.objects.filter(username=obj.username).exists():
                    user = Client.objects.create(username=obj.username)
                    user.is_active = True
                    user.email = obj.email
                    user.set_password(obj.password)
                    user.save()
                    obj.activated = True
                    obj.save()
                    return HttpResponseRedirect(redirect_to=f'{django_settings.APPLICATION_FRONT_URL}/success-registration')
        return HttpResponseRedirect(redirect_to=f'{django_settings.APPLICATION_FRONT_URL}/fail-registration')


class ClientViewSet(viewsets.ReadOnlyModelViewSet, CheckPermissions):
    serializer_class = ClientSerializer
    permission_classes = (IsAuthenticated,)
    strict_actions = ['list', 'retrieve']

    def get_queryset(self):
        return Client.objects.filter(
            id__in=[self.request.user.id] + list(self.request.user.employees.all().values_list('id', flat=True))
        )

    @action(detail=False, methods=['post', 'get'], url_path='write-off')
    def write_off(self, request):
        if request.user.username == 'admin':
            count = 0
            for client in Client.objects.filter(employer__isnull=True, is_superuser=False):
                if client.balance > 0:
                    Transaction.objects.create(client=client, desc=Transaction.TRANS_TYPE_1, value=client.tariff)
                    count += 1

            return Response({'data': f'{count} абонентских плат списано'}, status=200)
        return Response({'data': False})


class EmployeeViewSet(viewsets.ModelViewSet, CheckPermissions):
    serializer_class = EmployeeSerializer
    permission_classes = (IsAuthenticated,)
    strict_actions = ['list', 'retrieve', 'create']

    def get_queryset(self):
        return Client.objects.filter(employer_id=self.request.user.id)

    def create(self, request, *args, **kwargs):
        result = super().create(request, *args, **kwargs)
        user = Client.objects.get(id=result.data['id'])
        user.employer = request.user
        user.username = f'{request.user.username}_{user.username}'
        user.is_active = True
        user.set_password(request.data['password'])
        user.save()
        return result

    @action(detail=True, methods=['post'], url_path='set-password')
    def set_password(self, request, pk):
        user = self.get_queryset().filter(id=pk).first()
        user.set_password(request.data['password'])
        user.save()
        result = ResponseSchema(response_message='Данные обновлены')
        return Response(result.dict(), status=200)

    @action(detail=True, methods=['post'], url_path='share-gateway-lines')
    def share_gateway_lines(self, request, pk):
        update_shared_items(request, 'gateway', pk)
        result = ResponseSchema(response_message='Данные обновлены')
        return Response(result.dict(), status=200)

    @action(detail=True, methods=['post'], url_path='share-smb-slots')
    def share_smb_slots(self, request, pk):
        update_shared_items(request, 'smb', pk)
        result = ResponseSchema(response_message='Данные обновлены')
        return Response(result.dict(), status=200)


class OperatorViewSet(viewsets.ReadOnlyModelViewSet, CheckPermissions):
    queryset = Operator.objects.all()
    serializer_class = OperatorSerializer
    permission_classes = (IsAuthenticated,)
    strict_actions = ['list', 'retrieve']


class SimbankSchedulerViewSet(viewsets.ModelViewSet, CheckPermissions):
    serializer_class = SimbankSchedulerSerializer
    permission_classes = (IsAuthenticated,)
    strict_actions = ['list', 'retrieve', 'get_all_sms', 'partial_update']
    
    def get_queryset(self):
        return SimbankScheduler.objects.filter(client=self.request.user)

    @action(detail=False, methods=['get'])
    def get_all_sms(self, request):
        if SimbankScheduler.objects.filter(client=request.user).exists() and SimbankScheduler.objects.filter(client=request.user).first().server:
            result = get_all_sms(request)
            return Response(result)
        return Response([])
    @action(detail=False, methods=['get'])
    def get_all_call(self, request):
        if SimbankScheduler.objects.filter(client=request.user).exists() and SimbankScheduler.objects.filter(client=request.user).first().server:
            result = get_all_call(request)
            return Response(result)
        return Response([])

    @action(detail=True, methods=['post'], url_path='reboot-clo-server')
    def reboot_server(self, request, pk):
        reboot_clo_server(self.get_object())
        return Response(self.serializer_class(self.get_object()).data)

    @action(detail=False, methods=['post'], url_path='create-clo-server')
    def create_clo_server(self, request):
        if not SimbankScheduler.objects.filter(client=request.user).exists():
            if request.user.balance > 500:
                result = create_clo_server(request.user)
            else:
                return Response(ResponseSchema(
                    response_message='Не достаточно средств для создания сервера').dict(),
                    status=400)
            if result:
                return Response(ResponseSchema(response_message='Сервер создается, в течении 15 минут он появится в вашем кабинете').dict(), status=200)
            return Response(
                ResponseSchema(
                    response_message='Ошибка при создании сервера, обратитесь к администратору в телеграмм <a style="color: #fff;" href="https://t.me/simbank_pro" target="_blank">https://t.me/simbank_pro</a>').dict(),
                    status=400
            )
        return Response(
            ResponseSchema(response_message='У вас уже есть сервер').dict(),
            status=400)


class SimbankViewSet(viewsets.ModelViewSet, CheckPermissions):
    serializer_class = SimbankSerializer
    permission_classes = (IsAuthenticated,)
    strict_actions = ['list', 'retrieve', 'create']

    def get_queryset(self):
        return Simbank.objects.filter(client=self.request.user)


class GoipViewSet(viewsets.ModelViewSet, CheckPermissions):
    serializer_class = GoipSerializer
    permission_classes = (IsAuthenticated,)
    strict_actions = ['list', 'retrieve', 'state', 'create']

    def get_queryset(self):
        return Goip.objects.filter(client=self.request.user)

    @action(detail=False, methods=['get'])
    def state(self, request):
        """ Get all slots from goip """
        if SimbankScheduler.objects.filter(client=request.user).exists() and SimbankScheduler.objects.filter(client=request.user).first().server: # noqa
            data = map(lambda x: extend_gateway_item_with_operator_info(request.user.id, x), get_gateway_slots(request.user))
            return Response(data)
        return Response([])


class SimViewSet(viewsets.ModelViewSet, CheckPermissions):
    serializer_class = SimSerializer
    permission_classes = (IsAuthenticated,)
    strict_actions = ['list', 'retrieve', 'delete', 'activate_sim', 'upload_sim']

    def get_queryset(self):
        if UserVar.get():
            available_sim = []
            for it in UserVar.get().available_slots.through.objects.all().values_list('slots', flat=True):
                available_sim += it
            return Sim.objects.filter(smb_slot__in=available_sim)
        return Sim.objects.filter(client=self.request.user)

    @action(detail=False, methods=['post'])
    def delete(self, request):
        deleted = self.get_queryset().filter(id__in=request.data.get('ids', [])).delete()[0]
        return Response({'deleted': deleted}, status=204)

    @action(detail=True, methods=['post'])
    def activate_sim(self, request, pk):
        result: ResponseSchema = activate_sim(self.get_object(), int(request.data.get('line_id', 0)))
        if result.data.get('status'):
            return Response(result.dict(), status=200)
        return Response(result.dict(), status=400)

    @action(detail=True, methods=['post'])
    def send_ussd(self, request, pk):
        result: ResponseSchema = send_ussd(
            SimbankScheduler.objects.get(client=request.user).server,
            request.data.get('line_id', 0),
            request.data.get('msg', '')
        )
        return Response(result.dict(), status=200)

    @action(detail=True, methods=['post'])
    def send_sms(self, request, pk):
        result: ResponseSchema = send_sms(
            SimbankScheduler.objects.get(client=request.user).server,
            request.data.get('line_id', 0),
            request.data.get('msg', ''),
            request.data.get('phone')
        )
        if result.data.get('status'):
            return Response(result.dict(), status=200)
        return Response(result.dict(), status=400)

    @action(detail=False, methods=['post', 'get'])
    def upload_sim(self, request):
        if SimbankScheduler.objects.filter(client=request.user).exists() and SimbankScheduler.objects.filter(client=request.user).first().server:
            data = fill_sim_from_smb(request)
            return Response({'created': data})
        return Response({'created': 0})


class TransactionViewSet(viewsets.ReadOnlyModelViewSet, CheckPermissions):
    serializer_class = TransactionSerializer
    permission_classes = (IsAuthenticated,)
    strict_actions = []

    def get_queryset(self):
        return Transaction.objects.filter(client=self.request.user)


class BankRequestAPIView(views.APIView):
    permission_classes = (AllowAny,)
    serializer_class = BankRequestSerializer
    strict_actions = []

    def post(self, request): # noqa
        client = Client.objects.filter(username=request.data.get('username', '')).first()
        if int(request.data.get('value', 0)) < 10:
            return Response(ResponseSchema(response_message='Минимальная сумма платежа 100 рублей').dict(), status=400)
        if not client:
            return Response(ResponseSchema(response_message='Такого пользователя не существует').dict(), status=400)

        br = BankRequest.objects.create(value=request.data.get('value', 0), client=client)
        data = {
            'userName': django_settings.PAYMENT_LOGIN,
            'password': django_settings.PAYMENT_PASSWORD,
            'orderNumber': f'#{br.id + 1000500}',
            'amount': int(br.value) * 100,
            'returnUrl': f'{django_settings.BACKEND_URL}/api/payment-success',
            'failUrl': f'{django_settings.BACKEND_URL}/api/payment-failure'
        }

        request_data = requests.post('https://payment.alfabank.ru/payment/rest/register.do', data=data)
        if not request_data.json().get('errorMessage'):
            br.bank_id = request_data.json().get('orderId')
            br.save()
            return Response(ResponseSchema(data={'url': request_data.json().get('formUrl')}).dict())
        return Response(ResponseSchema(data=request_data.json(), response_message='Ошибка при пополнение баланса, обратитесь к администратору').dict(), status=400)


class PaymentSuccess(views.APIView):
    permission_classes = (AllowAny,)
    strict_actions = []

    def get(self, request): # noqa
        if request.GET.get('orderId'):
            data = {
                'userName': django_settings.PAYMENT_LOGIN,
                'password': django_settings.PAYMENT_PASSWORD,
                'orderId': request.GET.get('orderId')
            }

            request_data = requests.post('https://payment.alfabank.ru/payment/rest/getOrderStatusExtended.do', data=data)
            if request_data.json().get('orderStatus') == 2:
                if BankRequest.objects.filter(bank_id=request.GET.get('orderId'), payed=False).exists():
                    order = BankRequest.objects.get(bank_id=request.GET.get('orderId'), payed=False)
                    order.payed = True
                    order.save()
                return HttpResponseRedirect(redirect_to=f'{django_settings.APPLICATION_FRONT_URL}/success-payment')
        return HttpResponseRedirect(redirect_to=f'{django_settings.APPLICATION_FRONT_URL}/failure-payment')


class PaymentFail(views.APIView):
    permission_classes = (AllowAny,)
    strict_actions = []

    def get(self, request):  # noqa
        return HttpResponseRedirect(redirect_to=f'{django_settings.APPLICATION_FRONT_URL}/failure-payment')
