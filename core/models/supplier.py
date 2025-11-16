
from .base import BaseModel
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Supplier(BaseModel):
    supplier_code = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=128, blank=True, null=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(max_length=500, blank=True, null=True)
    tax_code = models.CharField(max_length=20, blank=True, null=True)
    payment_terms = models.CharField(max_length=255, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    total_debt = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    rating = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    class Meta:
        db_table = 'supplier'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['supplier_code']),
            models.Index(fields=['name', 'is_active']),
        ]

    def __str__(self):
        return f"{self.supplier_code} - {self.name}"
