from rest_framework import serializers
from django.utils.timezone import now

class CreateDebitSerializer(serializers.Serializer):
    customer_code = serializers.CharField(required=True)
    debit_amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=True)
    due_date = serializers.DateField(required=True)
    note = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_debit_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Số tiền nợ phải lớn hơn 0")
        return value

    def validate_due_date(self, value):
        today = now().date()
        if value < today:
            raise serializers.ValidationError("Ngày trả nợ không được là ngày trong quá khứ")
        return value