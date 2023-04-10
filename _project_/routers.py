from rest_framework.routers import DefaultRouter
from core.views import (
    ClientViewSet,
    GoipViewSet,
    OperatorViewSet,
    SimViewSet,
    SimbankSchedulerViewSet,
    SimbankViewSet,
    EmployeeViewSet,
    TransactionViewSet
)
from support.views import TicketViewSet, TicketMessageViewSet


router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'employee', EmployeeViewSet, basename='employee')
router.register(r'gateway', GoipViewSet, basename='gateway')
router.register(r'scheduler', SimbankSchedulerViewSet, basename='SimBank-Scheduler')
router.register(r'smb', SimbankViewSet, basename='SimBank')
router.register(r'operator', OperatorViewSet, basename='operator')
router.register(r'sim', SimViewSet, basename='sim')
router.register(r'transactions', TransactionViewSet, basename='transactions')
router.register(r'ticket', TicketViewSet, basename='ticket')
router.register(r'ticket-message', TicketMessageViewSet, basename='ticket-message')
