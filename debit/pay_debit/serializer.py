
from rest_framework import serializers


class PayDebitSerializer(serializers.Serializer):
    customer_code = serializers.CharField(
        required=True,
        error_messages={
            'blank': 'UUID khách hàng không được trống',
            'required': 'UUID khách hàng là bắt buộc'
        }
    )
    paid_amount = serializers.DecimalField(
        max_digits=19,
        decimal_places=5,
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
        return value
