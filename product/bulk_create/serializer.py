from rest_framework import serializers
from ..models import Product, Category


class BulkProductSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=True)
    sku = serializers.CharField(max_length=64, required=True)
    barCode = serializers.CharField(
        max_length=64, required=True, source='bar_code')
    category = serializers.CharField(max_length=255, required=True)
    costPrice = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=True, source='cost_price')
    price = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=True)
    quantity = serializers.IntegerField(required=True, source='stock_quantity')
    unit = serializers.CharField(max_length=50, required=True)

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Tên sản phẩm không được để trống")
        return value.strip()

    def validate_sku(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("SKU không được để trống")
        return value.strip()

    def validate_barCode(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Barcode không được để trống")
        return value.strip()

    def validate_costPrice(self, value):
        if value <= 0:
            raise serializers.ValidationError("Giá nhập phải lớn hơn 0")
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Giá bán phải lớn hơn 0")
        return value

    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Số lượng không được âm")
        return value


class BulkCreateProductsSerializer(serializers.Serializer):
    products = BulkProductSerializer(many=True, required=True)

    def validate_products(self, value):
        if not value:
            raise serializers.ValidationError(
                "Danh sách sản phẩm không được để trống")

        if len(value) > 1000:
            raise serializers.ValidationError(
                "Không thể thêm quá 1000 sản phẩm cùng lúc")

        barcodes = [p['bar_code'] for p in value]
        if len(barcodes) != len(set(barcodes)):
            raise serializers.ValidationError(
                "Có barcode bị trùng lặp trong danh sách")

        skus = [p['sku'] for p in value]
        if len(skus) != len(set(skus)):
            raise serializers.ValidationError(
                "Có SKU bị trùng lặp trong danh sách")

        return value
