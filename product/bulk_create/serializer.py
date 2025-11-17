from rest_framework import serializers


class BulkProductSerializer(serializers.Serializer):
    name = serializers.CharField(
        max_length=255, required=True, trim_whitespace=True)
    sku = serializers.CharField(
        max_length=64, required=True, trim_whitespace=True)
    barCode = serializers.CharField(
        max_length=64, required=True, trim_whitespace=True)
    category = serializers.CharField(
        max_length=255, required=True, trim_whitespace=True)
    costPrice = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=True)
    price = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=True)
    quantity = serializers.IntegerField(required=True)
    unit = serializers.CharField(
        max_length=50, required=True, trim_whitespace=True)

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Tên sản phẩm không được để trống")
        return value.strip()

    def validate_sku(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("SKU không được để trống")
        return value.strip().upper()

    def validate_barCode(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Barcode không được để trống")
        return value.strip()

    def validate_category(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Phân loại không được để trống")
        return value.strip()

    def validate_unit(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Đơn vị không được để trống")
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

        return value
