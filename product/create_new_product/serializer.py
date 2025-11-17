from rest_framework import serializers


class ProductCreateSerializer(serializers.Serializer):
    productName = serializers.CharField(
        max_length=255, required=True, trim_whitespace=True)
    sku = serializers.CharField(
        max_length=64, required=True, trim_whitespace=True)
    barCode = serializers.CharField(
        max_length=64, required=True, trim_whitespace=True)
    category = serializers.CharField(
        max_length=255, required=True, trim_whitespace=True)
    categoryId = serializers.IntegerField(required=False, allow_null=True)
    unit = serializers.CharField(
        max_length=50, required=True, trim_whitespace=True)
    costPrice = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=True)
    price = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=True)
    quantity = serializers.IntegerField(required=True)
    reorderPoint = serializers.IntegerField(required=True)
    maxStockLevel = serializers.IntegerField(required=True)
    supplierId = serializers.IntegerField(required=False, allow_null=True)
    image = serializers.URLField(
        max_length=500, required=False, allow_blank=True)
    description = serializers.CharField(
        required=False, allow_blank=True, trim_whitespace=True)
    hasExpiry = serializers.BooleanField(default=False)
    shelfLifeDays = serializers.IntegerField(required=False, allow_null=True)

    def validate_productName(self, value):
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

    def validate_reorderPoint(self, value):
        if value < 0:
            raise serializers.ValidationError("Điểm đặt lại không được âm")
        return value

    def validate_maxStockLevel(self, value):
        if value <= 0:
            raise serializers.ValidationError("Tồn kho tối đa phải lớn hơn 0")
        return value

    def validate_shelfLifeDays(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError(
                "Thời hạn sử dụng phải lớn hơn 0")
        return value

    def validate(self, data):
        if data.get('costPrice', 0) >= data.get('price', 0):
            raise serializers.ValidationError({
                'price': 'Giá bán phải lớn hơn giá nhập'
            })

        if data.get('reorderPoint', 0) >= data.get('maxStockLevel', 0):
            raise serializers.ValidationError({
                'reorderPoint': 'Điểm đặt lại phải nhỏ hơn tồn kho tối đa'
            })

        if data.get('hasExpiry') and not data.get('shelfLifeDays'):
            raise serializers.ValidationError({
                'shelfLifeDays': 'Vui lòng nhập thời hạn sử dụng khi sản phẩm có HSD'
            })

        return data
