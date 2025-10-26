from django.db import models
from .base import BaseModel
from .customer import Customer

class Debit(BaseModel):
    debit_amount = models.DecimalField(max_digits=19, decimal_places=5)
    note = models.TextField(max_length=255)
    paid_amount = models.DecimalField(max_digits=19, decimal_places=5)
    total_amount = models.DecimalField(max_digits=19, decimal_places=5)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT
    )
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'debit'

    def __str__(self):
        return f"Debit {self.id} - {self.customer} - {self.debit_amount}"
