from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager
)

class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("Phone number is required")
        phone_number = str(phone_number).strip()
        extra_fields.setdefault('is_active', True)

        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone_number, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    phone_number = models.CharField(
        _('phone number'),
        max_length=15,
        unique=True,
        blank=False,
        null=False
    )

    email = models.EmailField(_('email address'), blank=True, null=True)
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name  = models.CharField(_('last name'), max_length=150, blank=True)

    is_active = models.BooleanField(_('active'), default=True)
    is_staff  = models.BooleanField(_('staff status'), default=False)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    created_at  = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at  = models.DateTimeField(_('updated at'), auto_now=True)

    objects = UserManager()

    USERNAME_FIELD  = 'phone_number'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        db_table = 'user'
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return self.phone_number
