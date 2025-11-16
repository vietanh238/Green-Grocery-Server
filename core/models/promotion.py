
from .base import BaseModel
from django.db import models
from .product import Product
from .category import Category


class Promotion(BaseModel):
    promo_code = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Phần trăm'),
        ('fixed', 'Số tiền cố định'),
    ]
    discount_type = models.CharField(
        max_length=32,
        choices=DISCOUNT_TYPE_CHOICES
    )

    discount_value = models.DecimalField(max_digits=15, decimal_places=2)

    min_purchase_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    max_discount_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )

    usage_limit = models.IntegerField(null=True, blank=True)
    used_count = models.IntegerField(default=0)

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    applicable_products = models.ManyToManyField(
        Product,
        blank=True,
        related_name='promotions'
    )
    applicable_categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name='promotions'
    )

    class Meta:
        db_table = 'promotion'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['promo_code']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.promo_code} - {self.name}"
