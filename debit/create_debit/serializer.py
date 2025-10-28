from rest_framework import serializers
from django.utils.timezone import now


class CreateDebitSerializer(serializers.Serializer):
    customer_code = serializers.CharField(
        required=True,
        error_messages={
            'blank': 'UUID khách hàng không được trống',
            'required': 'UUID khách hàng là bắt buộc'
        }
    )
    debit_amount = serializers.DecimalField(
        max_digits=19,
        decimal_places=5,
        required=True,
        error_messages={
            'required': 'Số tiền nợ là bắt buộc',
            'invalid': 'Số tiền nợ phải là số'
        }
    )
    due_date = serializers.DateField(
        required=True,
        error_messages={
            'required': 'Ngày trả nợ là bắt buộc',
            'invalid_format': 'Định dạng ngày không hợp lệ (YYYY-MM-DD)'
        }
    )
    note = serializers.CharField(
        required=False,
        allow_blank=True,
        default=''
    )

    def validate_debit_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Số tiền nợ phải lớn hơn 0")
        return value

    def validate_due_date(self, value):
        today = now().date()
        if value < today:
            raise serializers.ValidationError(
                "Ngày trả nợ không được là ngày trong quá khứ")
        return value
