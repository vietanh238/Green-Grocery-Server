from django.db import models
from .base import BaseModel
from .category import Category

class Product(BaseModel):
    order = models.OneToOneField(
        'core.Order',
        on_delete=models.SET_NULL,
        null=True,
        related_name='payment'
    )
    name = models.CharField(max_length=255, unique=True, db_index=True)
    sku = models.CharField(max_length=64, unique=True, db_index=True)
    bar_code = models.CharField(max_length=64, unique=True, db_index=True)
    category_id = models.ForeignKey(
        Category,
        on_delete=models.PROTECT
    )
    unit = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    stock_quantity = models.IntegerField(default=0)
    reorder_point = models.IntegerField(default=0)

    class Meta:
        db_table = 'product'

    def __str__(self):
        pass