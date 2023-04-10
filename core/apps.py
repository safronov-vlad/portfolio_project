from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self) -> None:
        # from .signals import (
        #     create_auth_token,
        #     create_smb_sign,
        #     create_gateway_sign,
        #     delete_smb_sign,
        #     delete_gateway_sign,
        #     delete_clo_server,
        #     update_server_sign,
        #     create_transaction_sign,
        #     update_bank_request_sign
        # )
        return super().ready()
