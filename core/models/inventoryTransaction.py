from .base import BaseModel
from django.db import models
from .product import Product


class InventoryTransaction(BaseModel):
    TRANSACTION_TYPE_CHOICES = [
        ('import', 'Nhập hàng'),
        ('export', 'Xuất hàng'),
        ('adjustment', 'Điều chỉnh'),
        ('return', 'Trả hàng'),
        ('damage', 'Hư hỏng'),
        ('lost', 'Mất hàng'),
    ]

    transaction_code = models.CharField(
        max_length=64, unique=True, db_index=True)
    transaction_type = models.CharField(
        max_length=32,
        choices=TRANSACTION_TYPE_CHOICES,
        db_index=True
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='inventory_transactions'
    )

    quantity = models.IntegerField()
    quantity_before = models.IntegerField()
    quantity_after = models.IntegerField()

    unit_price = models.DecimalField(
        max_digits=15, decimal_places=2, default=0)
    total_value = models.DecimalField(
        max_digits=15, decimal_places=2, default=0)

    reference_type = models.CharField(max_length=50, blank=True, null=True)
    reference_id = models.IntegerField(blank=True, null=True)

    note = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'inventory_transaction'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_code']),
            models.Index(fields=['product', 'transaction_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.transaction_code} - {self.transaction_type}"
