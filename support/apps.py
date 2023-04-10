from django.apps import AppConfig


class SupportConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'support'

    def ready(self) -> None:
        from .signals import (
            create_ticket,
            create_ticket_message,
        )
        return super().ready()