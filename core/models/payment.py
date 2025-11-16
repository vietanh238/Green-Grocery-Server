from .base import BaseModel
from django.db import models
from .order import Order


class Payment(BaseModel):
    payment_code = models.CharField(max_length=64, unique=True, db_index=True)

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='payments',
        null=True,
        blank=True
    )

    amount = models.DecimalField(max_digits=15, decimal_places=2)

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Tiền mặt'),
        ('transfer', 'Chuyển khoản'),
        ('qr', 'Quét mã QR'),
        ('card', 'Thẻ'),
    ]
    payment_method = models.CharField(
        max_length=32,
        choices=PAYMENT_METHOD_CHOICES
    )

    STATUS_CHOICES = [
        ('pending', 'Đang xử lý'),
        ('completed', 'Hoàn thành'),
        ('failed', 'Thất bại'),
        ('refunded', 'Đã hoàn tiền'),
    ]
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )

    transaction_id = models.CharField(max_length=128, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)

    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'payment'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment_code']),
            models.Index(fields=['order', 'status']),
        ]

    def __str__(self):
        return f"Payment {self.payment_code} - {self.amount}"
