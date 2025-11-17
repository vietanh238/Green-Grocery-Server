# product/get_product/serializers.py
from rest_framework import serializers
from core.models import Product


class ProductListSerializer(serializers.ModelSerializer):
    max_stock = serializers.IntegerField(source='max_stock_level')

    # Hoặc nếu bạn muốn thêm các computed properties
    is_reorder = serializers.ReadOnlyField()
    is_overstock = serializers.ReadOnlyField()
    profit_per_unit = serializers.ReadOnlyField()
    profit_margin = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'bar_code', 'category', 'supplier',
            'unit', 'cost_price', 'price', 'stock_quantity',
            'reorder_point', 'max_stock',
            'image', 'description', 'has_expiry', 'shelf_life_days',
            'total_sold', 'total_revenue', 'is_reorder', 'is_overstock',
            'profit_per_unit', 'profit_margin', 'created_at', 'updated_at'
        ]
