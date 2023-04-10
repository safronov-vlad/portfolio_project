from rest_framework import viewsets
from rest_framework.exceptions import NotAuthenticated
from django.conf import settings


class CheckPermissions(viewsets.ViewSet):
    def initial(self, request, *args, **kwargs):
        if not (request.META.get('HTTP_ORIGIN', '-1') in settings.APPLICATION_FRONT_URL or request.user.is_superuser):
            if not self.action in self.strict_actions: # noqa
                raise NotAuthenticated(detail='Учетные данные не были предоставлены')

        if request.user.balance < 0:
            raise NotAuthenticated(detail={'response_message': 'Пополните баланс'})
        super().initial(request, *args, **kwargs)
