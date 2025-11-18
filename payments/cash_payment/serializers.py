from rest_framework import serializers
from core.models import Payment, Order, OrderItem, Product
from django.db import transaction
from django.utils import timezone


class PaymentItemSerializer(serializers.Serializer):
    bar_code = serializers.CharField(max_length=64, required=True)
    sku = serializers.CharField(max_length=64, required=True)
    name = serializers.CharField(max_length=255, required=True)
    quantity = serializers.IntegerField(min_value=1, required=True)
    unit_price = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=True)
    total_price = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=True)

    def validate_bar_code(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Barcode không được để trống")
        return value.strip()

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Số lượng phải lớn hơn 0")
        return value

    def validate_unit_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Đơn giá phải lớn hơn 0")
        return value


class CashPaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=True)
    items = PaymentItemSerializer(many=True, required=True)
    payment_method = serializers.ChoiceField(
        choices=['cash', 'transfer'],
        default='cash',
        required=False
    )
    note = serializers.CharField(
        max_length=500, required=False, allow_blank=True)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Số tiền phải lớn hơn 0")
        return value

    def validate_items(self, value):
        if not value or len(value) == 0:
            raise serializers.ValidationError(
                "Đơn hàng phải có ít nhất 1 sản phẩm")
        return value
