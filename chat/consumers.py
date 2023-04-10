import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django_redis import get_redis_connection as grc
from rest_framework.authtoken.models import Token
from core.equipment import get_gateway_slots, get_limited_slots_data, extend_gateway_item_with_operator_info
from core.models import Client, SimbankScheduler
from core.authentication import UserVar


class ConsumerMixin:

    def __init__(self):
        self.room_name: str = ''
        self.room_group_name: str = ''
        self.user: Client | None = None
        self.employee: bool = False

    def authorize_user(self):
        # Авторизация и установка данных
        token_key = dict((x.split('=') for x in self.scope['query_string'].decode().split("&"))).get('token', None) # noqa
        user_token = Token.objects.get(key=token_key)
        if user_token.user.employer:
            self.employee = True
            UserVar.set(user_token.user)
            self.user = user_token.user.employer
            # self.room_name = user_token.user.employer_id
        else:
            self.user = user_token.user
            self.employee = False
        self.room_name = user_token.user_id

        self.room_group_name = f"{self.scope['path'].split('/')[2]}_{self.room_name}"


class ChatConsumer(WebsocketConsumer, ConsumerMixin):
    def connect(self):
        # авторизуем пользователя
        self.authorize_user()
        # процесс присвоения главного пользователя
        #is_main = self.set_main_user()
        # создаем подключение
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )
        self.accept()
        # если только, что был присвоен юзер, просим данные
#        if is_main:
#            self.get_and_send_data()

    def disconnect(self, close_code):
        # убираем главного
        self.set_main_user(True)
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    def receive(self, text_data): # noqa
        # получение сообщения от пользователя
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        if message == 'get_data':
            self.get_and_send_data()

    def get_data(self):
        #redis = grc()
        #main_user = redis.get(self.room_group_name)
        data = []
        # если юзер главный то запрашивает новое состояние слотов
        #if main_user and int(main_user) == self.user.id:
        request_user = self.user
        if self.user.employer:
            request_user = self.user.employer
        data = map(lambda x: extend_gateway_item_with_operator_info(request_user.id, x), get_gateway_slots(request_user))
        # async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
        #     "type": "chat.message",
        #     "message": data
        # })
        #redis.expire(self.room_group_name, 30)
        return data
        # если нет главного, присваиваем и заново просим данные
        # elif not main_user:
        #     if self.set_main_user():
        #         data = self.get_data()
        # return data

    def set_main_user(self, left=False) -> bool:
        redis = grc()
        # получаем главного юзера, того кто будет тащить данные с сервера
        main_user = redis.get(self.room_group_name)
        # если ушел обнуляем
        if left:
            redis.set(self.room_group_name, '', 30)
            return False
        # устанавливем юзера если его нету
        if not main_user:
            redis.set(self.room_group_name, self.user.id, 30)
            return True
        return False

    def get_and_send_data(self):
        if SimbankScheduler.objects.filter(client=self.user).exists() and SimbankScheduler.objects.filter(client=self.user).first().server: # noqa
            data = list(map(lambda x: extend_gateway_item_with_operator_info(self.user.id, x), get_gateway_slots(self.user)))
            self.send(text_data=json.dumps(
                {"message": data}
            ))
        else:
            self.send(text_data=json.dumps(
                {"message": []}
            ))
        # result = get_gateway_slots(self.user)
        # req_user = self.user if self.employee else None
        # data = list(map(lambda x: extend_gateway_item_with_operator_info(req_user.id, x), get_limited_slots_data(result, req_user)))
        # self.send(text_data=json.dumps(
        #     {"message": data}
        # ))

    def chat_message(self, event):
        message = event["message"]
        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message}))


class ServerConsumer(WebsocketConsumer, ConsumerMixin):
    def connect(self):
        # авторизуем пользователя
        self.authorize_user()
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    def chat_message(self, event):
        message = event["message"]
        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message}))
