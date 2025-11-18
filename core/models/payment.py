from django.db import models
from django.conf import settings
from .base import BaseModel

User = settings.AUTH_USER_MODEL


class Payment(BaseModel):
    order = models.ForeignKey(
        'Order',
        on_delete=models.CASCADE,
        related_name='payments',
        null=True,
        blank=True
    )

    order_code = models.CharField(max_length=64, unique=True, db_index=True)
    transaction_id = models.CharField(max_length=128, blank=True, null=True)

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Tiền mặt'),
        ('qr', 'QR Code'),
        ('transfer', 'Chuyển khoản'),
        ('debt', 'Công nợ'),
    ]
    payment_method = models.CharField(
        max_length=32,
        choices=PAYMENT_METHOD_CHOICES,
        default='cash'
    )

    amount = models.DecimalField(max_digits=15, decimal_places=2)
    paid_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0)

    STATUS_CHOICES = [
        ('pending', 'Đang chờ'),
        ('paid', 'Đã thanh toán'),
        ('failed', 'Thất bại'),
        ('cancelled', 'Đã hủy'),
        ('delete', 'Đã xóa'),
    ]
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )

    description = models.TextField(blank=True, null=True)
    qr_code_url = models.URLField(max_length=500, blank=True, null=True)
    checkout_url = models.URLField(max_length=500, blank=True, null=True)

    paid_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'payment'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_code']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['transaction_id']),
        ]

    def __str__(self):
        return f"Payment {self.order_code} - {self.status}"
