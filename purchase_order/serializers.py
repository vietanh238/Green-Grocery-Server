from rest_framework import serializers
from core.models import PurchaseOrder, PurchaseOrderItem, Product, Supplier


class PurchaseOrderItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(min_value=1, required=True)
    unit_price = serializers.DecimalField(max_digits=15, decimal_places=2, required=True)
    total_price = serializers.DecimalField(max_digits=15, decimal_places=2, required=True)
    note = serializers.CharField(max_length=500, required=False, allow_blank=True)


class CreatePurchaseOrderSerializer(serializers.Serializer):
    supplier_id = serializers.IntegerField(required=True)
    expected_date = serializers.DateField(required=True)
    items = PurchaseOrderItemSerializer(many=True, required=True)
    note = serializers.CharField(required=False, allow_blank=True)


class PurchaseOrderListSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    supplier_code = serializers.CharField(source='supplier.supplier_code', read_only=True)
    supplier_phone = serializers.CharField(source='supplier.phone', read_only=True)
    items_count = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'po_code', 'supplier_name', 'supplier_code', 'supplier_phone',
            'status', 'total_amount', 'paid_amount', 'expected_date',
            'received_date', 'note', 'items_count', 'created_at', 'created_by_name'
        ]

    def get_items_count(self, obj):
        return obj.items.count()

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.last_name or obj.created_by.username
        return 'N/A'


class PurchaseOrderItemDetailSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product_unit = serializers.CharField(source='product.unit', read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id', 'product_id', 'product_name', 'product_sku', 'product_unit',
            'quantity', 'received_quantity', 'unit_price', 'total_price', 'note'
        ]


class PurchaseOrderDetailSerializer(serializers.ModelSerializer):
    supplier = serializers.SerializerMethodField()
    items = PurchaseOrderItemDetailSerializer(many=True, read_only=True)
    created_by_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrder
        fields = '__all__'

    def get_supplier(self, obj):
        return {
            'id': obj.supplier.id,
            'name': obj.supplier.name,
            'code': obj.supplier.supplier_code,
            'phone': obj.supplier.phone,
            'email': obj.supplier.email,
            'address': obj.supplier.address
        }

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.last_name or obj.created_by.username
        return 'N/A'

    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return obj.approved_by.last_name or obj.approved_by.username
        return None


