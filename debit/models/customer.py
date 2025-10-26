from django.db import models
from .base import BaseModel

class Customer(BaseModel):

    class DebtStatus(models.TextChoices):
        NO_DEBT = 'no_debt', 'Không nợ'
        IN_DEBT = 'in_debt', 'Đang nợ'
        PAID_DEBT = 'paid_debt', 'Đã trả nợ'
        OVERDUE = 'overdue', 'Nợ quá hạn'

    customer_code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255, blank=False)
    phone = models.CharField(max_length=50, null=False, blank=False)
    address = models.TextField(max_length=255, blank=True, default='', null=True)

    class Meta:
        db_table = 'customer'

    def __str__(self):
        return self.name
