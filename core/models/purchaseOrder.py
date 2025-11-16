
from .base import BaseModel
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .supplier import Supplier
from django.conf import settings
User = settings.AUTH_USER_MODEL


class PurchaseOrder(BaseModel):
    po_code = models.CharField(max_length=64, unique=True, db_index=True)

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='purchase_orders'
    )

    STATUS_CHOICES = [
        ('draft', 'Nháp'),
        ('pending', 'Chờ duyệt'),
        ('approved', 'Đã duyệt'),
        ('received', 'Đã nhận hàng'),
        ('cancelled', 'Đã hủy'),
    ]
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True
    )

    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    paid_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    expected_date = models.DateField()
    received_date = models.DateField(null=True, blank=True)

    note = models.TextField(blank=True, null=True)

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_purchase_orders'
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'purchase_order'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['po_code']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"PO {self.po_code} - {self.supplier.name}"
