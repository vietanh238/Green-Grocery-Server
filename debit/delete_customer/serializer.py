
from rest_framework import serializers


class DeleteCustomerSerializer(serializers.Serializer):
    customer_code = serializers.CharField(
        required=True,
        error_messages={
            'blank': 'UUID khách hàng không được trống',
            'required': 'UUID khách hàng là bắt buộc'
        }
    )
