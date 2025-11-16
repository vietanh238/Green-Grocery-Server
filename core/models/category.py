from .base import BaseModel
from django.db import models

class Category(BaseModel):

    name = models.CharField(max_length=255, unique=True, db_index=True)



    class Meta:
        db_table = 'category'

    def __str__(self):
        pass