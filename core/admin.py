from django.contrib import admin
from core.models import Client, SimbankScheduler, Simbank, Sim, Operator, Goip, AvailableSmbSlots, AvailableLines, Transaction, RegistrationRequest, BankRequest


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Основные', {"fields": ['username', 'password', 'email', 'phone', 'employer', 'balance', 'tariff', 'is_active', 'goip_mode']}),
        ('Административные', {"fields": ['is_superuser', 'is_staff', 'is_tech_support']})
    ]
    list_display = ('username', 'balance', 'is_active', 'is_superuser', 'employer')

admin.site.register(SimbankScheduler)
admin.site.register(Simbank)
admin.site.register(Sim)
admin.site.register(Operator)
admin.site.register(Goip)
admin.site.register(Transaction)
admin.site.register(AvailableSmbSlots)
admin.site.register(AvailableLines)
admin.site.register(BankRequest)
@admin.register(RegistrationRequest)
class RegistrationRequestAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Основные', {"fields": ['username', 'email', 'password', 'activated']}),
    ]
    list_display = ('username', 'activated')
