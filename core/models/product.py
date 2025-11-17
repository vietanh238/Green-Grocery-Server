from django.db import models
from .base import BaseModel
from .category import Category
from .supplier import Supplier
from django.core.validators import MinValueValidator
from decimal import Decimal


class Product(BaseModel):
    name = models.CharField(max_length=255, db_index=True)
    sku = models.CharField(max_length=64, unique=True, db_index=True)
    bar_code = models.CharField(max_length=64, unique=True, db_index=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products'
    )

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )

    unit = models.CharField(max_length=50)

    cost_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))]
    )

    price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))]
    )

    stock_quantity = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )

    reorder_point = models.IntegerField(
        default=10,
        validators=[MinValueValidator(0)]
    )

    max_stock_level = models.IntegerField(
        default=1000,
        validators=[MinValueValidator(0)]
    )

    image = models.URLField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    has_expiry = models.BooleanField(default=False)
    shelf_life_days = models.IntegerField(null=True, blank=True)

    total_sold = models.IntegerField(default=0)
    total_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    class Meta:
        db_table = 'product'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['bar_code']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['stock_quantity']),
        ]

    def __str__(self):
        return f"{self.sku} - {self.name}"

    @property
    def is_reorder(self):
        return 0 < self.stock_quantity <= self.reorder_point

    @property
    def is_overstock(self):
        return self.stock_quantity > self.max_stock_level

    @property
    def profit_per_unit(self):
        return self.price - self.cost_price

    @property
    def profit_margin(self):
        if self.cost_price > 0:
            return ((self.price - self.cost_price) / self.cost_price) * 100
        return 0
