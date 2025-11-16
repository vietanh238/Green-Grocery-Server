from django.db import models
from .base import BaseModel
from .customer import Customer
from .order import Order


class Debt(BaseModel):
    debt_code = models.CharField(max_length=64, unique=True, db_index=True)

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='debts'
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='debts'
    )

    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    paid_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0)
    debt_amount = models.DecimalField(max_digits=15, decimal_places=2)

    due_date = models.DateField()

    STATUS_CHOICES = [
        ('active', 'Đang nợ'),
        ('partial', 'Trả một phần'),
        ('paid', 'Đã trả'),
        ('overdue', 'Quá hạn'),
    ]
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True
    )

    note = models.TextField(blank=True, null=True)

    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'debt'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['debt_code']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return f"Debt {self.debt_code} - {self.customer.name}"
