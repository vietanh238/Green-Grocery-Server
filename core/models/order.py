# orders/models.py

from django.db import models
from django.conf import settings
from .base import BaseModel
from .customer import Customer
User = settings.AUTH_USER_MODEL

class Order(BaseModel):
    order_code = models.CharField(max_length=64, unique=True, db_index=True)

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )

    STATUS_CHOICES = [
        ('pending', 'Đang chờ'),
        ('paid', 'Đã thanh toán'),
        ('failed', 'Thất bại'),
        ('cancelled', 'Đã hủy'),
        ('refunded', 'Đã hoàn tiền'),
    ]
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )

    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    change_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Tiền mặt'),
        ('transfer', 'Chuyển khoản'),
        ('qr', 'Quét mã QR'),
        ('debt', 'Công nợ'),
    ]
    payment_method = models.CharField(
        max_length=32,
        choices=PAYMENT_METHOD_CHOICES,
        default='cash'
    )

    buyer_name = models.CharField(max_length=128, blank=True, null=True)
    buyer_phone = models.CharField(max_length=32, blank=True, null=True)

    note = models.TextField(blank=True, null=True)

    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'order'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_code']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['customer', 'status']),
        ]

    def __str__(self):
        return f"Order {self.order_code} - {self.status}"