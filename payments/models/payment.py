from .base import BaseModel
from django.db import models

class Payment(BaseModel):
    order_code = models.CharField(max_length=64, unique=True)
    amount = models.PositiveIntegerField()
    status = models.CharField(max_length=32, default="pending")
    transaction_id = models.CharField(max_length=128, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    buyer_name = models.CharField(max_length=128, blank=True, null=True)
    buyer_phone = models.CharField(max_length=32, blank=True, null=True)
    items = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'payment'
