# serializer.py
from rest_framework import serializers
from decimal import Decimal


class PayDebitSerializer(serializers.Serializer):
    customer_code = serializers.CharField(
        required=True,
        error_messages={
            'blank': 'Mã khách hàng không được trống',
            'required': 'Mã khách hàng là bắt buộc'
        }
    )
    paid_amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=True,
        error_messages={
            'required': 'Số tiền trả là bắt buộc',
            'invalid': 'Số tiền trả phải là số'
        }
    )
    note = serializers.CharField(
        required=False,
        allow_blank=True,
        default=''
    )

    def validate_paid_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Số tiền trả phải lớn hơn 0")
        return Decimal(str(value))
