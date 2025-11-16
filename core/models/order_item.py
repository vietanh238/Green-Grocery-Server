
from django.db import models
from django.conf import settings
from .base import BaseModel
from .order import Order
from .product import Product

User = settings.AUTH_USER_MODEL


class OrderItem(BaseModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items'
    )

    product_name = models.CharField(max_length=255, blank=True, null=True)
    product_sku = models.CharField(max_length=100, blank=True, null=True)

    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'order_item'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.quantity} x {self.product_name} (@ {self.price})"

    def save(self, *args, **kwargs):
        if self.product and not self.product_name:
            self.product_name = self.product.name
            self.product_sku = self.product.sku
        super().save(*args, **kwargs)
