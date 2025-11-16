from .base import BaseModel
from django.db import models


class Category(BaseModel):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    image = models.URLField(max_length=500, blank=True, null=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = 'category'
        verbose_name_plural = 'Categories'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['name', 'is_active']),
        ]

    def __str__(self):
        return self.name
