import re
import requests
from core.models import Simbank, SimbankScheduler, Sim, Goip, AvailableLines, AvailableSmbSlots, Client, Transaction
from core.schemas import ResponseSchema
from .authentication import UserVar


def check_permissions(is_employee: bool, data: list, value: int | str):
    if not is_employee:
        return True
    return value in data


# АВТОРЗИАЦИЯ
def smb_session(smb_path: str):
    session = requests.Session()
    session.post('http://{}/smb_scheduler/dologin.php'.format(smb_path), data={ # noqa
        'username': 'admin',
        'password': 'admin',
        'Submit': 'Sign',
        'lan': 3
    })
    return session.cookies


def gateway_session(gateway_path: str):
    session = requests.Session()
    session.post('http://{}/goip/dologin.php'.format(gateway_path), data={ # noqa
        'username': 'root',
        'password': 'root',
        'Submit': 'Sign in',
        'lan': 3
    })
    return session.cookies


# СОЗДАНИЕ УДАЛЕНИЕ
def create_smb(obj: Simbank):
    url = "http://{}/smb_scheduler/en/sim_bank.php?action=saveadd".format(obj.smb_server.server) # noqa
    requests.post(url, cookies=smb_session(obj.smb_server.server), data={
        'name': obj.smb_id,
        'simbank_tag': obj.name,
        'Password': obj.password,
        'banktype': f'SMB{obj.get_smb_type_display()}',
        'team_id': 0,
        'imei_mode': 0,
        'imei_prefix': '',
        'month_limit_time': '',
        'month_reset_day': '',
        'remain_time': '',
        'time_unit': 60,
        'count_limit': '',
        'no_connected_limit': '',
        'no_ring_limit': '',
        'no_answer_limit': '',
        'short_call_limit': '',
        'short_time': '',
        'Action': 'Modify',
        'Submit': 'Add'
    })


def create_gateway(obj: Goip):
    server_path = obj.smb_server.server
    # добавить шлюз в шедулер
    url = "http://{}/smb_scheduler/en/rm_device.php?action=saveadd".format(server_path) # noqa
    requests.post(url, cookies=smb_session(server_path), data={
        'name': obj.goip_id,
        'goip_tag': obj.name,
        'Password': obj.password,
        'goiptype': 'GoIPx{}'.format(obj.get_goip_type_display()),
        'team_id': 0,
        'zone': 0,
        'zone_tag': '',
        'Action': 'Modify',
        'Submit': 'Save'
    })
    # добавить шлюз в смс сервер
    url = "http://{}/goip/en/goip.php?action=saveadd".format(server_path) # noqa
    requests.post(url, cookies=gateway_session(server_path), data={
        'name': obj.goip_id,
        'line': int(obj.get_goip_type_display()),
        'provider': '1',
        'goip_group': '0',
        'Password': obj.password,
        'PwdConfirm': obj.password,
        'count_limit': '',
        'count_limit_d': '',
        'report_mail': '',
        'report_http': '',
        'Action': 'Modify',
        'Submit': '++Add++'
        })


def delete_smb(obj: Simbank) -> None:
    url = "http://{}/smb_scheduler/en/sim_bank.php?name={}&action=del".format(obj.smb_server.server, obj.smb_id) # noqa
    requests.post(url, cookies=smb_session(obj.smb_server.server))


def delete_gateway(obj: Goip) -> None:
    server_path = obj.smb_server.server
    # удалить с шедулера
    url = "http://{}/smb_scheduler/en/rm_device.php?name={}&action=del".format(server_path, obj.goip_id) # noqa
    # удалить с смс сервера
    requests.post(url, cookies=smb_session(server_path))
    url = "http://{}/goip/api_smb.php".format(server_path) # noqa
    requests.post(url, data={"action": "delete_goip", "goipid": obj.goip_id}) # noqa


def delete_server(obj: SimbankScheduler) -> None:
    # удалить сервер
    requests.delete(
        f'http://{settings.ANSIBLE_SERVER}/api/servers/{obj.ansible_server_id}/',
        headers={'Authorization': settings.ANSIBLE_SERVER_TOKEN}
    )


def check_sims_smb_active(request) -> list:
    schedulers = SimbankScheduler.objects.filter(client=request.user)
    data = list()
    for s in schedulers:
        if request.user.goip_mode:
            url = 'http://{}/goip/api_smb.php'.format(s.server) # noqa
            response = requests.post(url, data={'action': 'check_sim_smb'})
        else:
            url = 'http://{}/smb_scheduler/api.php?get=check_sim_smb'.format(s.server) # noqa
            response = requests.get(url)
        for res in response.text.split(';'):
            data.append(res)

    return data


def fill_sim_from_smb(request) -> int:
    data = check_sims_smb_active(request)
    created = 0
    to_create = []
    for d in data:
        if d != '':
            if Sim.objects.filter(client=request.user, smb_slot=int(d)).exists():
                Sim.objects.filter(client=request.user, smb_slot=int(d)).update(status=True)
                continue

            if request.user.goip_mode:
                to_create.append(Sim(name=d, smb_slot=int(d), goip_id=int(d), status=True, client=request.user))
            else:
                if len(d) == 5:
                    smb = Simbank.objects.filter(client=request.user, smb_id=int(d[:2])).first()
                elif len(d) == 6:
                    smb = Simbank.objects.filter(client=request.user, smb_id=int(d[:3])).first()
                else:
                    smb = Simbank.objects.filter(client=request.user, smb_id=int(d[0])).first()
                to_create.append(Sim(name=d, smb_slot=int(d), goip_id=int(d), smb=smb, status=True, client=request.user))

    if to_create:
        created = len(Sim.objects.bulk_create(to_create))
    return created


def create_clo_server(user: Client) -> bool:
    result = SimbankScheduler.objects.create(clo_server=True, install_progress='Сервер устанавливается: 0%', client=user, name=f'{user.username}_smb')
    server_request = requests.post(
        f'http://{settings.ANSIBLE_SERVER}/api/servers/',
        headers={'Authorization': settings.ANSIBLE_SERVER_TOKEN},
        data={'name': result.name, 'simbankpro_id': result.id, 'callback_token': user.auth_token.key} # noqa
    )
    #Transaction.objects.create(client=user, )
    if server_request.status_code == 201:
        if server_request.json().get('errors', False):
            requests.delete(
                f'http://{settings.ANSIBLE_SERVER}/api/servers/{server_request.json().get("id")}',
                headers={'Authorization': settings.ANSIBLE_SERVER_TOKEN},
            )
            result.delete()
            return False
        return True
    return False


def reboot_clo_server(obj: SimbankScheduler) -> bool:
    requests.patch(
        f'http://{settings.ANSIBLE_SERVER}/api/servers/{obj.ansible_server_id}/',
        headers={'Authorization': settings.ANSIBLE_SERVER_TOKEN},
        data={'rebooting': True}
    )
    obj.rebooting = True
    obj.save()
    return True


def get_lines_data(gateway_mode: bool, scheduler: SimbankScheduler) -> list:
    slots_data = []
    if gateway_mode:
        result = requests.post(
            "http://{}/goip/api_smb.php".format(scheduler.server), # noqa
            data={'action': 'get_goip'}
        ).text.split(';')
    else:
        result = requests.get(
            "http://{}/smb_scheduler/api?get=goip_status".format(scheduler.server),  # noqa
            cookies=gateway_session(scheduler.server)
        ).text.split(';')
    # Если gateway_mode переворачиваем список
    if gateway_mode:
        result = list(reversed(result))

    # Данные по слотам
    for slot_item in result:
        slot_data = slot_item.split(',')
        if len(slot_data) > 1:
            line_data = {
                'line_id': slot_data[5],
                'login': slot_data[0],
                'gsm_status': slot_data[1],
                'operator': slot_data[7],
                'signal': slot_data[8],
                'sim_id': slot_data[6], # slot_data[5] if gateway_mode else
                'imei': slot_data[9]
            }
            slots_data.append(line_data)
    return slots_data


# ДАННЫЕ
def get_gateway_slots(client: Client, get_full=False) -> list:
    """
        Информация по приходяшим данным по слотам
        names = {
            0: 'line_id',
            1: 'login',
            2: 'gsm_status',
            3: 'operator',
            4: 'signal',
            8: 'sim_id',
            9: 'imei'
        }
    """
    scheduler = SimbankScheduler.objects.filter(client=client).first()
    if scheduler:
        slots_data = get_lines_data(client.goip_mode, scheduler)
        if get_full:
            return slots_data
        return get_limited_slots_data(slots_data, UserVar.get())
    return []


def get_limited_slots_data(data: list, is_employee: Client | None) -> list:
    # ограничиние доступных слотов сотрудникам
    allowed_lines: list = []
    if is_employee:
        for it in is_employee.available_lines.through.objects.filter(client=UserVar.get()).values_list('lines', flat=True):
            allowed_lines += it
    new_list = []
    for item in data:
        if check_permissions(bool(is_employee), allowed_lines, item['line_id']):
            new_list.append(item)
    return new_list


def extend_gateway_item_with_operator_info(user_id: int, item: dict) -> dict:
    try:
        sim = Sim.objects.get(goip_id=int(item['sim_id']), client_id=user_id)
        item['id'] = sim.id
        # item['operator_instance'] = OperatorSerializer(
        #     instance=sim.operator,
        #     context={'request': request}
        # ).data
        item['phone_number'] = sim.name
        return item
    except Exception:
        return item


def get_all_sms(request) -> list:
    url = "http://{}/goip/api_smb.php".format(SimbankScheduler.objects.filter(client=request.user).first().server) # noqa get_all_sms_employee
    payload = {
        'action': 'get_all_sms',
        'start': request.GET.get('start'),
        'end': request.GET.get('end')
    }
    if UserVar.get():
        payload['action'] = 'get_all_sms_employee'
        available_lines = []
        for it in UserVar.get().available_lines.through.objects.all().values_list('lines', flat=True):
            available_lines += it
        payload['ports'] = ','.join(available_lines)

    get_sms = requests.post(url, data=payload)
    result = list()
    if get_sms.text:
        sim_data = {}
        for sms in get_sms.text.split("/;/"):
            s = sms.split("/,/")
            result.append({
                'sms_sender': s[0],
                'datetime': s[1],
                'content': s[2],
                'phone': sim_data.get(s[3], s[3])
            })
    return result


def get_all_call(request) -> list:
    url = "http://{}/smb_scheduler/api.php?get=get_all_call&start={}&end={}".format(
        SimbankScheduler.objects.filter(client=request.user).first().server,
        '2022-11-01 00:00',#request.GET.get('start'),
        '2023-02-03 00:00'#request.GET.get('end')
    ) # noqa get_all_sms_employee
    # if UserVar.get():
    #     payload['action'] = 'get_all_sms_employee'
    #     available_lines = []
    #     for it in UserVar.get().available_lines.through.objects.all().values_list('lines', flat=True):
    #         available_lines += it
    #     payload['ports'] = ','.join(available_lines)

    get_call = requests.post(url)
    result = []
    if get_call.text:
        for sms in get_call.text.split("/;/"):
            s = sms.split("/,/")
            result.append({
                'line_id': s[0],
                'datetime': s[1],
                'number': s[2],
                'sim_name': s[3]
            })
    return result


# ДЕЙСТВИЯ
def check_sim_status(obj: Sim) -> int:
    server_path = obj.smb.smb_server.server
    url = 'http://{}/smb_scheduler/api.php?get=sim_slot&sim={}'.format(server_path, obj.smb_slot) # noqa
    response = requests.get(url, cookies=smb_session(server_path))
    if response.text == '':
        return 0
    return int(response.text)


def modify_sim(obj: Sim, line: int = None) -> str:
    server_path = obj.smb.smb_server.server
    if line:
        url = 'http://{}/smb_scheduler/api.php?set=bind&sim={}&line={}'.format(server_path, obj.smb_slot, line) # noqa
    else:
        url = 'http://{}/smb_scheduler/api.php?set=bind&sim={}'.format(server_path, obj.smb_slot) # noqa

    response = requests.post(url, cookies=smb_session(server_path))
    return response.text


def activate_sim(obj: Sim, gateway_line: int = None) -> ResponseSchema:
    # проверка статуса симкарты
    if check_sim_status(obj) in [0, 12]:  # если статус активен или готовится
        obj.status = False
        obj.save()
        return ResponseSchema(data={'status': False}, response_message=f'Симкарта не найдена - {obj.name} ({obj.smb_slot})')
    # извлекаем симкарту
    if 'OK.bind' not in modify_sim(obj):
        return ResponseSchema(data={'status': False}, response_message=f'Не удалось извлечь симкарту - {obj.name} ({obj.smb_slot})')
    # если line не указана останавливаемся
    if not gateway_line:
        obj.status = True
        obj.save()
        return ResponseSchema(data={'status': True}, response_message=f'Симкарта извлечена - {obj.name} ({obj.smb_slot})')
    # вставляем симкарту
    if 'OK.bind' not in modify_sim(obj, gateway_line):
        return ResponseSchema(data={'status': False}, response_message=f'Не удалось вставить симкарту - {obj.name} ({obj.smb_slot})')
    obj.status = True
    obj.save()
    return ResponseSchema(data={'status': True}, response_message=f'Симкарта активирована - {obj.name} ({obj.smb_slot})')


def send_ussd(server:str, gateway_line, msg: str) -> ResponseSchema:
    url = 'http://{}/goip/api_smb.php?debug=1&TERMID={}'.format(server, gateway_line) # noqa
    data = {'USSDMSG': msg, 'action': 'send_ussd'}
    response = requests.post(url, data)

    return ResponseSchema(response_message=response.text)


def send_sms(server_path: str, gateway_line, msg: str, phone: str) -> ResponseSchema:
    try:
        urls = {
            'api_smb': "http://%s/goip/api_smb.php" % server_path, # noqa
            'create_send': "http://%s/goip/en/dosend.php" % server_path, # noqa
            'finish_send': "http://%s/goip/en/resend.php?messageid=%s&USERNAME=&PASSWORD=" # noqa
        }
        # получаем внутренний goip id отправителя
        sender_id = requests.post(urls['api_smb'], data={'action': 'get_goip_id', 'name': gateway_line}).text # noqa
        # создаем задание на отправку
        requests.post(urls['create_send'], cookies=gateway_session(server_path), data={
            'method': '2',
            'smsnum': phone,
            'smsprovider': '1',
            'smsgoip': sender_id,
            'submit1': 'Send',
            'datehm': '',
            'qmsg': '',
            'Memo': msg
        })
        # получаем id письма отправки
        mes_id = requests.post(urls['api_smb'], data={'action': 'get_resend', 'phone': phone, 'goip_id': sender_id}).text # noqa
        # отправляем сообщение
        result = requests.post(urls['finish_send'] % (server_path, mes_id), cookies=gateway_session(server_path), data={
            'messageid': mes_id,
            'USERNAME': '',
            'PASSWORD': ''
        }).text
        if re.search(r'\bERROR\b', result):
            return ResponseSchema(data={'status': False}, response_message='Ошибка отправки смс')
        return ResponseSchema(data={'status': True}, response_message='смс отправлено')
    except Exception as exc: # noqa
        return ResponseSchema(data={'status': False}, response_message=exc)


# TODO - переписать функцию по человечески
def update_shared_items(request, obj: str, user_id: str) -> None:
    if obj == 'smb':
        AvailableSmbSlots.objects.filter(client_id=user_id).delete()
    for item in request.data.get('data', []):
        if obj == 'gateway':
            updated_items = item.get('lines', [])
            updated_items.sort()
            model = AvailableLines
            data = {
                'client': Client.objects.get(id=user_id),
                'gateway': Goip.objects.get(client=request.user, name=item.get('name', '')),
                'defaults': {'lines': updated_items}
            }
        else:
            model = AvailableSmbSlots
            smb = Simbank.objects.filter(id=item).first()
            updated_items = item
            if smb:
                updated_items = smb.get_slots()
                updated_items.sort()
            data = {
                'client': Client.objects.get(id=user_id),
                'smb': smb,
                'defaults': {'slots': updated_items}
            }

        if updated_items:
            model.objects.update_or_create(**data)
        else:
            data.pop('defaults')
            model.objects.filter(**data).delete()
