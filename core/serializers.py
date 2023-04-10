from rest_framework import serializers
from .models import Client, Goip, Operator, Sim, Simbank, SimbankScheduler, Transaction, BankRequest


class ClientSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Client
        fields = ('id', 'username', 'balance', 'goip_mode', 'employer', 'role')

    def get_role(self, obj): # noqa
        return 'employee' if obj.employer else 'owner'


class EmployeeSerializer(serializers.ModelSerializer):
    smb_slots = serializers.SerializerMethodField(read_only=True)
    gateway_lines = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Client
        fields = ('id', 'username', 'balance', 'goip_mode', 'employer', 'smb_slots', 'gateway_lines')

    def get_smb_slots(self, obj): # noqa
        return [{'data': i.smb.id, 'name': i.smb.name} for i in obj.available_slots.through.objects.filter(client=obj)]

    def get_gateway_lines(self, obj): # noqa
        return [{
                'name': i.gateway.name,
                'data': i.lines
            } for i in obj.available_lines.through.objects.filter(client=obj)]

class SimbankSchedulerSerializer(serializers.ModelSerializer): # noqa
    datetime = serializers.SerializerMethodField(read_only=True)

    def get_datetime(self, obj): # noqa
        return obj.datetime.strftime("%Y-%m-%d")

    class Meta:
        model = SimbankScheduler
        fields = '__all__'
    
    def validate(self, attrs):
        attrs['client'] = self.context['request'].user
        return attrs


class SimbankSerializer(serializers.ModelSerializer): # noqa
    slots = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Simbank
        fields = ('client', 'count_active', 'id', 'imeimode', 'name', 'password', 'smb_id', 'smb_type', 'smb_server', 'slots') # noqa

    def to_internal_value(self, data):
        data['client'] = self.context['request'].user.id
        data['name'] = f"SMB#{data['smb_id']}"
        data['smb_server'] = SimbankScheduler.objects.get(client=self.context['request'].user).id
        return super().to_internal_value(data)


    def get_slots(self, obj): # noqa
        data = []
        for i in range(1, int(obj.get_smb_type_display()) + 1, 1):
            prefix = 1000 if obj.smb_type == 1 else 100
            data.append(str(i + obj.smb_id * prefix))

        return [str(i + obj.smb_id * 1000) for i in range(1, int(obj.get_smb_type_display()) + 1, 1)]


class GoipSerializer(serializers.ModelSerializer): # noqa

    lines = serializers.SerializerMethodField(read_only=True)

    def to_internal_value(self, data):
        data['client'] = self.context['request'].user.id
        data['name'] = f"GOIP#{data['goip_id']}"
        data['smb_server'] = SimbankScheduler.objects.get(client=self.context['request'].user).id
        return super().to_internal_value(data)

    def get_lines(self, obj):
        return [str(i + obj.goip_id * 100) for i in range(1, int(obj.get_goip_type_display()) + 1, 1)]

    class Meta:
        model = Goip
        fields = '__all__'


class SimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sim
        fields = ("id", "name", "add_dt", "status", "smb_slot", "goip_id", "client", "operator", "smb")
        
    def create(self, validated_data):
        validated_data['client'] = self.context['request'].user
        return super().create(validated_data)


class OperatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operator
        fields = '__all__'


class TransactionSerializer(serializers.ModelSerializer):
    type_str = serializers.SerializerMethodField(read_only=True)
    desc_str = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Transaction
        fields = ('type_str', 'type', 'desc_str', 'value', 'dt_create')

    def get_type_str(self, obj):
        return 'Пополнение' if obj.type else 'Списание'

    def get_desc_str(self, obj):
        return obj.get_desc_display()


class BankRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankRequest
        fields = '__all__'
