# admin.py

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from constants import EnrollmentStatus
from .models import Course, Lesson, Enrollment, Section, Teacher


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "teacher", "is_public")
    search_fields = ("name", "teacher__name")
    ordering = ("name",)
    autocomplete_fields = ["teacher"]


# Custom form cho Lesson để validate dữ liệu
class LessonAdminForm(forms.ModelForm):
    class Meta:
        model = Lesson
        # Ẩn trường thời lượng để chỉ tính tự động từ video (nếu có)
        exclude = ("duration_minutes",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["section"].required = True
        self.fields["section"].help_text = _(
            "Chọn phần cho bài học (ví dụ: Từ vựng, Ngữ pháp, Luyện đề, ...)"
        )

    def clean(self):
        cleaned_data = super().clean()
        errors = []

        if not cleaned_data.get("course"):
            errors.append(_("Bắt buộc chọn Course."))
        if not cleaned_data.get("section"):
            errors.append(_("Bắt buộc chọn Section."))
        if not cleaned_data.get("title"):
            errors.append(_("Bắt buộc nhập Lesson Title."))
        if cleaned_data.get("order") is None:
            errors.append(_("Bắt buộc nhập Thứ tự."))
        if not cleaned_data.get("video_url") and not cleaned_data.get("video_file"):
            errors.append(_("Bắt buộc nhập Video URL hoặc upload Video File."))

        if errors:
            raise ValidationError(errors)
        return cleaned_data


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    form = LessonAdminForm
    list_display = ("title", "course", "section", "order", "video_preview")
    list_filter = ("course", "section")
    autocomplete_fields = ["course", "section"]

    def video_preview(self, obj):
        """
        Preview nhỏ trong admin:
        - Nếu có video_url (YouTube): nhúng iframe.
        - Nếu có video_file: render <video>.
        - Nếu không: trả '-'.
        """
        if obj.video_url:
            yt_id = self._extract_youtube_id(obj.video_url)
            if yt_id:
                return format_html(
                    '<iframe width="200" height="113" '
                    'src="https://www.youtube.com/embed/{}" frameborder="0" '
                    'allowfullscreen></iframe>',
                    yt_id,
                )
        if obj.video_file:
            return format_html('<video width="200" controls src="{}"></video>', obj.video_file.url)
        return "-"

    video_preview.short_description = _("Preview")

    @staticmethod
    def _extract_youtube_id(url: str) -> str | None:
        """
        Tách YouTube ID đơn giản, hỗ trợ dạng:
        - https://www.youtube.com/watch?v=XXXX
        - https://youtu.be/XXXX
        Không cần quá phức tạp cho admin preview.
        """
        try:
            if "youtu.be/" in url:
                return url.split("youtu.be/")[-1].split("?")[0]
            if "watch?v=" in url:
                return url.split("watch?v=")[-1].split("&")[0]
        except Exception:
            return None
        return None


# Hành động duyệt / từ chối hàng loạt cho Enrollment
@admin.action(description=_("Approve selected enrollments"))
def approve(modeladmin, request, queryset):
    updated = queryset.update(
        status=EnrollmentStatus.APPROVED.value,
        approved_at=timezone.now(),
    )
    modeladmin.message_user(
        request, _("Approved %(n)d enrollment(s).") % {"n": updated}
    )


@admin.action(description=_("Reject selected enrollments"))
def reject(modeladmin, request, queryset):
    qs = queryset.exclude(status=EnrollmentStatus.REJECTED.value)
    updated = qs.update(status=EnrollmentStatus.REJECTED.value, approved_at=None)
    modeladmin.message_user(
        request, _("Rejected %(n)d enrollment(s).") % {"n": updated}
    )


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "status", "created_at", "approved_at")
    list_filter = ("status", "course")
    search_fields = ("user__username", "user__email", "course__name")
    raw_id_fields = ("user", "course")
    actions = [approve, reject]


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("name", "position")
    search_fields = ("name", "position")


# Section admin hỗ trợ autocomplete
@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    search_fields = ("title", "course__name")
    autocomplete_fields = ["course"]
