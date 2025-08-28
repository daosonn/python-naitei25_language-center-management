from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .models import User, UserProfile
from constants import ROLE_ADMIN, ROLE_WEBSITE_ADMIN

# Custom UserAdmin để ẩn group và bổ sung thông tin profile
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_filter = ('role', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password', 'role', 'is_active')}),
        (_('Thông tin cá nhân'), {
            'fields': (
                'profile_full_name', 'profile_phone_number', 'profile_japanese_level',
                'profile_display_name', 'profile_gender', 'profile_birthday', 'profile_avatar',
                'profile_active',
            )
        }),
        (_('Ngày giờ'), {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = (
        'profile_full_name', 'profile_phone_number', 'profile_japanese_level',
        'profile_display_name', 'profile_gender', 'profile_birthday', 'profile_avatar',
        'profile_active',
        'last_login', 'date_joined',
    )
    list_display = ('email', 'username', 'role', 'is_active')
    search_fields = ('email', 'username')
    ordering = ('-date_joined',)
    filter_horizontal = ('user_permissions',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'is_staff' in form.base_fields:
            form.base_fields.pop('is_staff')
        return form

    def get_fieldsets(self, request, obj=None):
        # Ẩn group và superuser khỏi giao diện admin
        fieldsets = super().get_fieldsets(request, obj)
        filtered = []
        for fs in fieldsets:
            if fs[0] == 'Groups':
                continue
            if fs[0] == 'Permissions':
                # Loại bỏ trường is_superuser khỏi permissions
                fs = (fs[0], {'fields': tuple(f for f in fs[1]['fields'] if f != 'is_superuser')})
            filtered.append(fs)
        return filtered

    # ====== Các trường profile hiển thị readonly (đều bọc i18n) ======
    def profile_full_name(self, obj):
        return obj.profile.full_name if hasattr(obj, 'profile') else ''
    profile_full_name.short_description = _('Họ và Tên')

    def profile_phone_number(self, obj):
        return obj.profile.phone_number if hasattr(obj, 'profile') else ''
    profile_phone_number.short_description = _('Số điện thoại')

    def profile_japanese_level(self, obj):
        return obj.profile.japanese_level if hasattr(obj, 'profile') else ''
    profile_japanese_level.short_description = _('Trình độ tiếng Nhật')

    def profile_display_name(self, obj):
        return obj.profile.display_name if hasattr(obj, 'profile') else ''
    profile_display_name.short_description = _('Tên hiển thị')

    def profile_gender(self, obj):
        return obj.profile.gender if hasattr(obj, 'profile') else ''
    profile_gender.short_description = _('Giới tính')

    def profile_birthday(self, obj):
        return obj.profile.birthday if hasattr(obj, 'profile') else ''
    profile_birthday.short_description = _('Ngày sinh')

    def profile_avatar(self, obj):
        if hasattr(obj, 'profile') and obj.profile.avatar:
            return format_html('<img src="{}" width="60" style="border-radius:50%;"/>', obj.profile.avatar.url)
        return ''
    profile_avatar.short_description = _('Ảnh đại diện')

    def profile_active(self, obj):
        if hasattr(obj, 'profile') and obj.profile.active:
            return format_html('<span style="color:green; font-weight:bold;">&#10004; {}</span>', _('Đang hoạt động'))
        return format_html('<span style="color:red; font-weight:bold;">&#10008; {}</span>', _('Bị khóa'))
    profile_active.short_description = _('Trạng thái')

    def profile_role(self, obj):
        if hasattr(obj, 'profile'):
            if obj.profile.role in (ROLE_ADMIN, ROLE_WEBSITE_ADMIN):
                return _('Admin')
            return _('User')
        return ''
    profile_role.short_description = _('Vai trò')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user_link', 'role_display', 'active_display',
        'full_name', 'phone_number', 'japanese_level',
        'display_name', 'gender', 'birthday', 'created_at',
    )
    search_fields = ('user__email', 'display_name', 'user__username')
    list_filter = ('gender', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'user_link', 'user_info', 'enrolled_courses')
    ordering = ('-created_at',)

    def user_link(self, obj):
        # Sửa lại app_label cho đúng với User model đăng ký admin (accounts.User)
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_link.short_description = _('Email người dùng')

    def user_info(self, obj):
        u = obj.user
        return format_html(
            '<b>{}</b> {}<br>'
            '<b>{}</b> {}<br>'
            '<b>{}</b> {}<br>'
            '<b>{}</b> {}<br>'
            '<b>{}</b> {}',
            _('Email:'), u.email,
            _('Tên đăng nhập:'), u.username,
            _('Ngày tham gia:'), u.date_joined.strftime('%d/%m/%Y'),
            _('Trạng thái:'), _('Hoạt động') if u.is_active else _('Bị khóa'),
            _('Vai trò:'), u.role,
        )
    user_info.short_description = _('Thông tin người dùng')

    def enrolled_courses(self, obj):
        enrollments = obj.user.enrollments.select_related('course').all()
        if not enrollments:
            return _('(Chưa đăng ký)')
        return format_html('<ul>{}</ul>', ''.join(f'<li>{e.course.name}</li>' for e in enrollments))
    enrolled_courses.short_description = _('Khóa học đang theo học')

    fieldsets = (
        (None, {
            'fields': (
                'user_link', 'user_info',
                'role_display', 'active_display',
                'full_name', 'phone_number', 'japanese_level',
                'display_name', 'gender', 'birthday', 'avatar', 'address', 'country',
                'created_at', 'updated_at',
            )
        }),
        (_('Khóa học đang theo học'), {
            'fields': ('enrolled_courses',),
            'classes': ('collapse',),
        }),
    )

    def role_display(self, obj):
        if obj.role in (ROLE_ADMIN, ROLE_WEBSITE_ADMIN):
            return _('Admin')
        return _('User')
    role_display.short_description = _('Vai trò')

    def active_display(self, obj):
        if obj.active:
            return format_html('<span style="color:green; font-weight:bold;">&#10004; {}</span>', _('Đang hoạt động'))
        return format_html('<span style="color:red; font-weight:bold;">&#10008; {}</span>', _('Bị khóa'))
    active_display.short_description = _('Trạng thái')

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields
