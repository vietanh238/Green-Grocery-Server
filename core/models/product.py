from django.db import models
from .base import BaseModel
from .category import Category
from .supplier import Supplier
from django.core.validators import MinValueValidator, MaxValueValidator
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
    reorder_quantity = models.IntegerField(
        default=50,
        validators=[MinValueValidator(0)]
    )

    max_stock = models.IntegerField(
        default=1000,
        validators=[MinValueValidator(0)]
    )

    image = models.URLField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    dimensions = models.CharField(max_length=100, blank=True, null=True)

    is_featured = models.BooleanField(default=False)
    is_best_seller = models.BooleanField(default=False)

    expiry_date = models.DateField(null=True, blank=True)
    manufacture_date = models.DateField(null=True, blank=True)

    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    total_sold = models.IntegerField(default=0)
    total_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    view_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'product'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku', 'bar_code']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['stock_quantity']),
            models.Index(fields=['-total_sold']),
        ]

    def __str__(self):
        return f"{self.sku} - {self.name}"

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.reorder_point

    @property
    def profit_margin(self):
        if self.cost_price > 0:
            return ((self.price - self.cost_price) / self.cost_price) * 100
        return 0
