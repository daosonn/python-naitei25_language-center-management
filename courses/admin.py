from .models import Teacher


from django.contrib import admin
from .models import Course, Lesson, Enrollment
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from constants import EnrollmentStatus

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'teacher', 'is_public')
    search_fields = ('name', 'teacher__name')
    ordering = ('name',)
    autocomplete_fields = ['teacher']

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'video_preview')

    def video_preview(self, obj):
        if obj.video_url:
            # chỉ lấy iframe cho YouTube
            return format_html(
                '<iframe width="200" height="113" src="https://www.youtube.com/embed/{}" frameborder="0"></iframe>',
                obj.video_url.split('v=')[-1]
            )
        if obj.video_file:
            return format_html('<video width="200" controls src="{}"></video>', obj.video_file.url)
        return "-"
    video_preview.short_description = _("Preview")


# Nút duyệt/từ chối hàng loạt
@admin.action(description=_("Approve selected enrollments"))
def approve(modeladmin, request, queryset):
    updated = queryset.update(
        status=EnrollmentStatus.APPROVED.value,
        approved_at=timezone.now()
    )
    modeladmin.message_user(request, _("Approved %(n)d enrollment(s).") % {"n": updated})

@admin.action(description=_("Reject selected enrollments"))
def reject(modeladmin, request, queryset):
    qs = queryset.exclude(status=EnrollmentStatus.REJECTED.value)
    updated = qs.update(status=EnrollmentStatus.REJECTED.value, approved_at=None)
    modeladmin.message_user(request, _("Rejected %(n)d enrollment(s).") % {"n": updated})

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "status", "created_at", "approved_at")
    list_filter  = ("status", "course")
    search_fields = ("user__username", "user__email", "course__name")
    raw_id_fields = ("user", "course")   
    actions = [approve, reject]

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'position')
    search_fields = ('name', 'position')