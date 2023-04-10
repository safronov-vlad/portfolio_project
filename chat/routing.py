# chat/routing.py
from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/gateway_state/$", consumers.ChatConsumer.as_asgi()),
    re_path(r"ws/server_state/$", consumers.ServerConsumer.as_asgi()),
]
