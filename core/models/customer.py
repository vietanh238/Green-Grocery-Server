from django.db import models
from .base import BaseModel
from django.core.validators import MinValueValidator, MaxValueValidator

class Customer(BaseModel):

    customer_code = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, db_index=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(max_length=500, blank=True, null=True)

    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[('male', 'Nam'), ('female', 'Nữ'), ('other', 'Khác')],
        blank=True,
        null=True
    )

    total_orders = models.IntegerField(default=0)
    total_spent = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    total_debt = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    CUSTOMER_TYPE_CHOICES = [
        ('regular', 'Thường'),
        ('vip', 'VIP'),
        ('wholesale', 'Bán sỉ'),
    ]
    customer_type = models.CharField(
        max_length=20,
        choices=CUSTOMER_TYPE_CHOICES,
        default='regular'
    )

    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    last_purchase_date = models.DateField(null=True, blank=True)

    note = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'customer'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer_code']),
            models.Index(fields=['phone']),
            models.Index(fields=['-total_spent']),
        ]

    def __str__(self):
        return f"{self.customer_code} - {self.name}"
