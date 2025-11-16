from rest_framework import serializers
from core.models import Customer

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'address']
        extra_kwargs = {
            'name': {
                'required': True,
                'error_messages': {
                    'blank': 'Tên khách hàng không được trống',
                    'required': 'Tên khách hàng là bắt buộc'
                }
            },
            'phone': {
                'required': True,
                'error_messages': {
                    'blank': 'Số điện thoại không được trống',
                    'required': 'Số điện thoại là bắt buộc'
                }
            },
            'address': {'required': False, 'allow_blank': True}
        }