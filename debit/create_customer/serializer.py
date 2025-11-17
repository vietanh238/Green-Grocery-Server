from rest_framework import serializers
from core.models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    def validate(self, data):
        error_code = 0
        if not data.get('phone'):
            error_code = 1
        is_has_account = Customer.objects.filter(
            phone=data.get('phone')
        ).first()
        if is_has_account:
            error_code = 2

        return error_code
