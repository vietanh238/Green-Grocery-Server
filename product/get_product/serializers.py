# product/get_product/serializers.py
from rest_framework import serializers
from core.models import Product


class ProductListSerializer(serializers.ModelSerializer):
    name_category = serializers.CharField(
        source='category.name', read_only=True)
    primary_supplier_name = serializers.CharField(
        source='supplier.name', read_only=True)

    is_reorder = serializers.ReadOnlyField()
    is_overstock = serializers.ReadOnlyField()
    profit_per_unit = serializers.ReadOnlyField()
    profit_margin = serializers.ReadOnlyField()
    stock_value = serializers.ReadOnlyField()
    stock_status = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'bar_code', 'name_category',
            'primary_supplier_name', 'unit', 'cost_price', 'price',
            'stock_quantity', 'reorder_point', 'max_stock_level',
            'image', 'description', 'has_expiry', 'shelf_life_days',
            'total_sold', 'total_revenue', 'is_reorder', 'is_overstock',
            'profit_per_unit', 'profit_margin', 'stock_value', 'stock_status',
            'last_restock_date', 'last_sold_date', 'created_at', 'updated_at'
        ]
