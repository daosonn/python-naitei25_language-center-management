from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver

from constants import (
    MAX_USERNAME_LENGTH,
    MAX_EMAIL_LENGTH,
    MAX_ROLE_LENGTH,
    MAX_NAME_LENGTH,
    MAX_GENDER_LENGTH,
    UserRole,
    Gender,
    MAX_TOKEN_LENGTH
)

class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError(_('Email là bắt buộc'))
        if not username:
            raise ValueError(_('Username là bắt buộc'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', UserRole.WEBSITE_ADMIN.value)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser phải có is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser phải có is_superuser=True.'))
        
        return self.create_user(email, username, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=MAX_USERNAME_LENGTH, unique=True, verbose_name=_("Tên đăng nhập"))
    email = models.EmailField(max_length=MAX_EMAIL_LENGTH, unique=True, verbose_name=_("Email"))
    is_blocked = models.BooleanField(default=False, verbose_name=_("Bị khóa"))
    role = models.CharField(
        max_length=MAX_ROLE_LENGTH, 
        choices=UserRole.choices(),
        default=UserRole.USER.value,
        verbose_name=_("Vai trò")
    )
    
    is_active = models.BooleanField(default=True, verbose_name=_("Hoạt động"))
    is_staff = models.BooleanField(default=False, verbose_name=_("Là nhân viên"))
    date_joined = models.DateTimeField(default=timezone.now, verbose_name=_("Ngày tham gia"))
    
    is_email_verified = models.BooleanField(default=False, verbose_name=_("Đã xác thực email"))
    email_verification_token = models.CharField(max_length=MAX_TOKEN_LENGTH, blank=True, null=True)
    
    password_reset_token = models.CharField(max_length=MAX_TOKEN_LENGTH, blank=True, null=True)
    password_reset_expires = models.DateTimeField(blank=True, null=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = _('Người dùng')
        verbose_name_plural = _('Người dùng')
    
    def __str__(self):
        return self.email
    
    def get_name(self):
        if hasattr(self, 'profile') and self.profile.display_name:
            return self.profile.display_name
        return self.username
    
    def can_login(self):
        return self.is_active and not self.is_blocked

class UserProfile(models.Model):
    full_name = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        verbose_name=_('Họ và Tên')
    )
    phone_number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name=_('Số điện thoại')
    )
    japanese_level = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name=_('Trình độ tiếng Nhật')
    )
    address = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        verbose_name=_('Địa chỉ')
    )
    country = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name=_('Quốc gia')
    )
    user = models.OneToOneField(
        User, 
        on_delete=models.RESTRICT, 
        related_name='profile',
        verbose_name=_("Người dùng")
    )
    display_name = models.CharField(
        max_length=MAX_NAME_LENGTH, 
        null=True, 
        blank=True,
        help_text=_("Tên hiển thị của người dùng"),
        verbose_name=_("Tên hiển thị")
    )
    gender = models.CharField(
        max_length=MAX_GENDER_LENGTH,
        choices=Gender.choices(),
        null=True,
        blank=True,
        verbose_name=_("Giới tính")
    )
    birthday = models.DateField(null=True, blank=True, verbose_name=_("Ngày sinh"))
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True, 
        blank=True,
        help_text=_("Ảnh đại diện của người dùng"),
        verbose_name=_("Ảnh đại diện")
    )
    # Trạng thái hoạt động: dùng user.is_active thay cho is_locked
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Tạo lúc"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Cập nhật lúc"))

    @property
    def role(self):
        return self.user.role if self.user else None

    @property
    def active(self):
        return self.user.is_active if self.user else False
    
    class Meta:
        verbose_name = _('Hồ sơ người dùng')
        verbose_name_plural = _('Hồ sơ người dùng')
    
    def __str__(self):
        return f"Profile of {self.user.username}"

    def get_name(self):
        return self.display_name or self.full_name or self.user.username

    def get_avatar(self):
        if self.avatar:
            return self.avatar.url
        else:
            return '/static/images/default-avatar.png'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
