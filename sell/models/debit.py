from django.db import models
from .base import BaseModel

class Debit(BaseModel):

    name = models.CharField(max_length=255, unique=True, db_index=True, null=False, blank=False)
    debit_amount = models.DecimalField(max_digits=19 ,decimal_places=5)
    note = models.TextField(max_length=255)
    paid_amount = models.DecimalField(max_digits=19 ,decimal_places=5)
    phone_number = models.CharField(
        max_length=15,
        unique=True,
    )
    total_amount = models.DecimalField(max_digits=19 ,decimal_places=5)

    class Meta:
        db_table = 'debit'

    def __str__(self):
        pass
