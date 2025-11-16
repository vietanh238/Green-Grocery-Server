
from .base import BaseModel
from django.db import models
from django.core.validators import MinValueValidator
from .purchaseOrder import PurchaseOrder
from .product import Product

class PurchaseOrderItem(BaseModel):
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='purchase_items'
    )

    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    received_quantity = models.IntegerField(default=0)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    total_price = models.DecimalField(max_digits=15, decimal_places=2)

    note = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'purchase_order_item'
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
