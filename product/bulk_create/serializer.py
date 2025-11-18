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
    reorderPoint = serializers.IntegerField(required=False, default=10)
    maxStockLevel = serializers.IntegerField(required=False, default=1000)
    supplierName = serializers.CharField(
        max_length=255, required=False, allow_blank=True, trim_whitespace=True)
    hasExpiry = serializers.BooleanField(required=False, default=False)
    shelfLifeDays = serializers.IntegerField(required=False, allow_null=True)

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

    def validate(self, data):
        if data.get('costPrice', 0) >= data.get('price', 0):
            raise serializers.ValidationError("Giá bán phải lớn hơn giá nhập")

        if data.get('hasExpiry') and not data.get('shelfLifeDays'):
            raise serializers.ValidationError(
                "Vui lòng nhập thời hạn sử dụng khi sản phẩm có HSD")

        return data


class BulkCreateProductsSerializer(serializers.Serializer):
    products = BulkProductSerializer(many=True, required=True)

    def validate_products(self, value):
        if not value:
            raise serializers.ValidationError(
                "Danh sách sản phẩm không được để trống")

        if len(value) > 1000:
            raise serializers.ValidationError(
                "Không thể thêm quá 1000 sản phẩm cùng lúc")

        barcodes = [p['barCode'] for p in value]
        skus = [p['sku'] for p in value]

        if len(barcodes) != len(set(barcodes)):
            raise serializers.ValidationError(
                "Có barcode bị trùng lặp trong danh sách")

        if len(skus) != len(set(skus)):
            raise serializers.ValidationError(
                "Có SKU bị trùng lặp trong danh sách")

        return value
