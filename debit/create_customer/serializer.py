from rest_framework import serializers
from core.models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    def validate(self, data):
        error_code = 0

        if not data.get('name') or not data.get('name').strip():
            error_code = 1
            return error_code

        if not data.get('phone') or not data.get('phone').strip():
            error_code = 3
            return error_code

        existing_customer = Customer.objects.filter(
            phone=data.get('phone').strip(),
            is_active=True
        ).first()

        if existing_customer:
            error_code = 2
            return error_code

        return error_code
