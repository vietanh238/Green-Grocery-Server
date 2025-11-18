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


class CreatePaymentSerializer(serializers.Serializer):
    orderCode = serializers.IntegerField(required=True)
    amount = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=True)
    description = serializers.CharField(
        max_length=500, required=False, allow_blank=True)
    returnUrl = serializers.URLField(required=True)
    cancelUrl = serializers.URLField(required=True)
    items = PaymentItemSerializer(many=True, required=True)
    buyerName = serializers.CharField(
        max_length=128, required=False, allow_blank=True)
    buyerPhone = serializers.CharField(
        max_length=20, required=False, allow_blank=True)

    def validate_orderCode(self, value):
        if value <= 0:
            raise serializers.ValidationError("Mã đơn hàng không hợp lệ")
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Số tiền phải lớn hơn 0")
        return value

    def validate_items(self, value):
        if not value or len(value) == 0:
            raise serializers.ValidationError(
                "Đơn hàng phải có ít nhất 1 sản phẩm")

        total_from_items = sum(item['total_price'] for item in value)

        return value


class PaymentDetailSerializer(serializers.ModelSerializer):
    order_items = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id', 'order_code', 'transaction_id', 'payment_method',
            'amount', 'paid_amount', 'status', 'description',
            'qr_code_url', 'checkout_url', 'paid_at',
            'created_at', 'updated_at', 'order_items'
        ]

    def get_order_items(self, obj):
        if obj.order:
            items = obj.order.items.all()
            return [{
                'product_name': item.product_name,
                'product_sku': item.product_sku,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'total_price': item.total_price,
            } for item in items]
        return []
