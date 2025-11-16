from .base import BaseModel
from django.db import models
from django.conf import settings
User = settings.AUTH_USER_MODEL


class ActivityLog(BaseModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activity_logs'
    )

    ACTION_CHOICES = [
        ('create', 'Tạo mới'),
        ('update', 'Cập nhật'),
        ('delete', 'Xóa'),
        ('login', 'Đăng nhập'),
        ('logout', 'Đăng xuất'),
        ('view', 'Xem'),
        ('export', 'Xuất dữ liệu'),
        ('import', 'Nhập dữ liệu'),
    ]
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)

    model_name = models.CharField(max_length=100)
    object_id = models.IntegerField(null=True, blank=True)
    object_repr = models.CharField(max_length=255, blank=True, null=True)

    changes = models.JSONField(null=True, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'activity_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.phone_number} - {self.action} - {self.model_name}"
