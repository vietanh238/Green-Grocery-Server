
from django.db import models
from django.conf import settings
from .base import BaseModel
from .order import Order
from .product import Product
from django.core.validators import MinValueValidator

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

    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=100)

    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    discount_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=15, decimal_places=2)

    cost_price = models.DecimalField(
        max_digits=15, decimal_places=2, default=0)
    profit = models.DecimalField(
        max_digits=15, decimal_places=2, default=0)

    class Meta:
        db_table = 'order_item'
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        if self.product and not self.product_name:
            self.product_name = self.product.name
            self.product_sku = self.product.sku
            self.cost_price = self.product.cost_price

        self.total_price = (
            self.unit_price * self.quantity) - self.discount_amount
        self.profit = (self.unit_price - self.cost_price) * self.quantity

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product_name} @ {self.unit_price}"
