from rest_framework import serializers
from core.models import Product, Category
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

class ProductSerializer(serializers.ModelSerializer):

    costPrice = serializers.DecimalField(
        source='cost_price',
        max_digits=10,
        decimal_places=2,
        required=True,
        error_messages={'required': 'Cost price is required.'}
    )

    barCode = serializers.CharField(
        source='bar_code',
        max_length=64,
        required=True,
        validators=[UniqueValidator(queryset=Product.objects.all(), message={
            "error_code": "001",
            "message": "barcode đã tồn tại"
        })],
        error_messages={'required': 'barcode is required.', 'blank': 'barCode is not blank', 'unique': 'A product with this barcode already exists.'}
    )

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'sku',
            'barCode',
            'category',
            'unit',
            'price',
            'stock_quantity',
            'costPrice',
            'created_at',
            'updated_at',
            'created_by'
        ]

        read_only_fields = ["id", "created_at", "updated_at", "created_by"]

        extra_kwargs = {
            'sku': {
                'error_messages': {'unique': 'A product with this SKU already exists.'}
            },
            'unit': {
                'required': True,
                'error_messages': {'required': 'Unit is required.'}
            },
            'name': {
                'required': True,
                'max_length': 64,
                'error_messages': {'required': 'Product name is required.', 'blank': 'Product name cannot be blank.', 'unique': 'adasd'}
            },
            'price': {
                'required': True,
                'max_digits': 10,
                'decimal_places': 2,
                'error_messages': {'required': 'Selling price is required.'}
            }
        }

    def validate(self, data):
        return data

    # def validate_name(self, value):
    #     qs = Product.objects.filter(name=value)
    #     if self.isins