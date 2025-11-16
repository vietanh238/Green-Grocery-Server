
from .base import BaseModel
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from .debt import Debt


class DebtPayment(BaseModel):
    payment_code = models.CharField(max_length=64, unique=True, db_index=True)

    debt = models.ForeignKey(
        Debt,
        on_delete=models.CASCADE,
        related_name='payments'
    )

    amount = models.DecimalField(max_digits=15, decimal_places=2)

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Tiền mặt'),
        ('transfer', 'Chuyển khoản'),
        ('qr', 'Quét mã QR'),
    ]
    payment_method = models.CharField(
        max_length=32,
        choices=PAYMENT_METHOD_CHOICES,
        default='cash'
    )

    note = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'debt_payment'
        ordering = ['-created_at']

    def __str__(self):
        return f"Debt Payment {self.payment_code} - {self.amount}"
