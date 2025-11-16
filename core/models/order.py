# orders/models.py

from django.db import models
from django.conf import settings
from .base import BaseModel

User = settings.AUTH_USER_MODEL


class Order(BaseModel):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    order_code = models.CharField(max_length=64, unique=True, db_index=True)
    STATUS_CHOICES = [
        ('pending', 'Đang chờ'),
        ('paid', 'Đã thanh toán'),
        ('failed', 'Thất bại'),
        ('cancelled', 'Đã hủy'),
    ]
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )

    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00)

    buyer_name = models.CharField(max_length=128, blank=True, null=True)
    buyer_phone = models.CharField(max_length=32, blank=True, null=True)

    note = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'order'
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_code} - {self.status}"
