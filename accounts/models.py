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
    MAX_TOKEN_LENGTH,
    UserRole,
    Gender,
    FULL_NAME_MAX_LENGTH,
    PHONE_NUMBER_MAX_LENGTH,
    JAPANESE_LEVEL_MAX_LENGTH,
    ADDRESS_MAX_LENGTH,
    COUNTRY_MAX_LENGTH,
)


class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password, **extra_fields):
        """
        Tạo người dùng thông thường (bắt buộc có mật khẩu).
        Admin nội bộ cũng dùng hàm này rồi gán is_staff/is_superuser nếu cần.
        """
        if not email:
            raise ValueError(_("Email là bắt buộc"))
        if not username:
            raise ValueError(_("Username là bắt buộc"))
        if not password:
            raise ValueError(_("Mật khẩu là bắt buộc"))

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user_unusable(self, email, username, **extra_fields):
        """
        Luồng SSO (chưa đặt mật khẩu): user chỉ đăng nhập qua social;
        sau này có thể đặt mật khẩu.
        """
        if not email:
            raise ValueError(_("Email là bắt buộc"))
        if not username:
            raise ValueError(_("Username là bắt buộc"))

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_unusable_password()
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        max_length=MAX_USERNAME_LENGTH,
        unique=True,
        verbose_name=_("Tên đăng nhập"),
    )
    email = models.EmailField(
        max_length=MAX_EMAIL_LENGTH,
        unique=True,
        verbose_name=_("Email"),
    )

    role = models.CharField(
        max_length=MAX_ROLE_LENGTH,
        choices=UserRole.choices(),
        default=UserRole.USER.value,
        verbose_name=_("Vai trò"),
    )

    is_active = models.BooleanField(default=True, verbose_name=_("Hoạt động"))
    is_staff = models.BooleanField(default=False, verbose_name=_("Là nhân viên"))
    is_blocked = models.BooleanField(default=False, verbose_name=_("Bị khóa"))
    date_joined = models.DateTimeField(default=timezone.now, verbose_name=_("Ngày tham gia"))

    is_email_verified = models.BooleanField(default=False, verbose_name=_("Đã xác thực email"))
    email_verification_token = models.CharField(
        max_length=MAX_TOKEN_LENGTH, blank=True, null=True, verbose_name=_("Mã xác thực email")
    )

    password_reset_token = models.CharField(
        max_length=MAX_TOKEN_LENGTH, blank=True, null=True, verbose_name=_("Mã đặt lại mật khẩu")
    )
    password_reset_expires = models.DateTimeField(blank=True, null=True, verbose_name=_("Hết hạn đặt lại mật khẩu"))

    objects = CustomUserManager()

    # Đăng nhập bằng email
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = _("Người dùng")
        verbose_name_plural = _("Người dùng")

    def __str__(self):
        return self.email

    def get_name(self):
        if hasattr(self, "profile") and self.profile.display_name:
            return self.profile.display_name
        return self.username

    def can_login(self):
        return self.is_active and not self.is_blocked


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,   # Xóa user sẽ xóa profile
        related_name="profile",
        verbose_name=_("Người dùng"),
    )
    is_locked = models.BooleanField(
        default=False,
        verbose_name=_("Bị khóa"),
        help_text=_("Khóa profile"),
    )

    display_name = models.CharField(
        max_length=MAX_NAME_LENGTH,
        null=True,
        blank=True,
        help_text=_("Tên hiển thị của người dùng"),
        verbose_name=_("Tên hiển thị"),
    )
    full_name = models.CharField(
        max_length=FULL_NAME_MAX_LENGTH,
        null=True,
        blank=True,
        verbose_name=_("Họ và Tên"),
    )
    gender = models.CharField(
        max_length=MAX_GENDER_LENGTH,
        choices=Gender.choices(),
        null=True,
        blank=True,
        verbose_name=_("Giới tính"),
    )
    birthday = models.DateField(null=True, blank=True, verbose_name=_("Ngày sinh"))

    phone_number = models.CharField(
        max_length=PHONE_NUMBER_MAX_LENGTH,
        null=True,
        blank=True,
        verbose_name=_("Số điện thoại"),
    )
    japanese_level = models.CharField(
        max_length=JAPANESE_LEVEL_MAX_LENGTH,
        null=True,
        blank=True,
        verbose_name=_("Trình độ tiếng Nhật"),
    )
    address = models.CharField(
        max_length=ADDRESS_MAX_LENGTH,
        null=True,
        blank=True,
        verbose_name=_("Địa chỉ"),
    )
    country = models.CharField(
        max_length=COUNTRY_MAX_LENGTH,
        null=True,
        blank=True,
        verbose_name=_("Quốc gia"),
    )
    avatar = models.ImageField(
        upload_to="avatars/",
        null=True,
        blank=True,
        help_text=_("Ảnh đại diện của người dùng"),
        verbose_name=_("Ảnh đại diện"),
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Tạo lúc"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Cập nhật lúc"))

    class Meta:
        verbose_name = _("Hồ sơ người dùng")
        verbose_name_plural = _("Hồ sơ người dùng")

    def __str__(self):
        return f"Profile of {self.user.username}"

    # Alias tương thích code cũ: profile.phone
    @property
    def phone(self):
        return self.phone_number

    @phone.setter
    def phone(self, value):
        self.phone_number = value

    def get_name(self):
        return self.display_name or self.full_name or self.user.username

    def get_avatar(self):
        return self.avatar.url if self.avatar else "/static/img/logo.png"


# Tự tạo profile khi user được tạo
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
