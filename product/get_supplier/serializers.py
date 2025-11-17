# product/supplier/serializers.py
from rest_framework import serializers
from core.models import Supplier


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            'id', 'supplier_code', 'name', 'contact_person', 'phone',
            'email', 'address', 'tax_code', 'bank_account', 'bank_name',
            'payment_terms', 'credit_limit', 'total_debt', 'note',
            'created_at', 'updated_at'
        ]

class SupplierCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            'supplier_code', 'name', 'contact_person', 'phone',
            'email', 'address', 'tax_code', 'bank_account', 'bank_name',
            'payment_terms', 'credit_limit', 'note'
        ]

    def validate_supplier_code(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Mã nhà cung cấp không được để trống")
        return value.strip()

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Tên nhà cung cấp không được để trống")
        return value.strip()

    def validate_phone(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Số điện thoại không được để trống")
        return value.strip()
