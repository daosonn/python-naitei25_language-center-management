from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from constants import (
    # Course & Lesson
    COURSE_NAME_MAX_LENGTH,
    COURSE_COVER_UPLOAD_PATH,
    COURSE_DEFAULT_ORDERING,
    LESSON_TITLE_MAX_LENGTH,
    LESSON_ORDER_DEFAULT,
    LESSON_VIDEO_UPLOAD_PATH,
    LESSON_DEFAULT_ORDERING,
    LESSON_UNIQUE_TOGETHER,
    LESSON_VIDEO_REQUIRED_MSG,

    # Section
    SECTION_TITLE_MAX_LENGTH,
    SECTION_ORDER_DEFAULT,

    # Enrollment
    MAX_STATUS_LENGTH,
    STATUS_CHOICES,
    ENROLLMENT_STATUS_MAX_LENGTH,
)


# ======================= COURSE ======================= #
class Course(models.Model):

    @property
    def duration_text(self):
        total_minutes = sum(l.total_duration_minutes for l in self.lessons.all())
        if total_minutes >= 60:
            hours = total_minutes // 60
            minutes = total_minutes % 60
            if minutes:
                return f"{hours} giờ {minutes} phút"
            return f"{hours} giờ"
        elif total_minutes > 0:
            return f"{total_minutes} phút"
        return "—"
    is_public = models.BooleanField(_('Public'), default=True, help_text=_('Bỏ chọn để ẩn khoá học này khỏi người dùng'))
    name = models.CharField(_("Course Name"), max_length=COURSE_NAME_MAX_LENGTH)
    slug = models.SlugField(_("Slug"), max_length=128, blank=True, null=True)
    description = models.TextField(_("Description"), blank=True)
    cover = models.ImageField(
        _("Cover Image"),
        upload_to=COURSE_COVER_UPLOAD_PATH,
        blank=True,
        null=True,
    )
    teacher = models.ForeignKey(
        "courses.Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses",
        verbose_name=_("Giảng viên"),
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Course")
        verbose_name_plural = _("Courses")
        ordering = COURSE_DEFAULT_ORDERING

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# ======================= SECTION ======================= #
class Section(models.Model):
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="sections",
    )
    title = models.CharField(max_length=SECTION_TITLE_MAX_LENGTH)
    order = models.PositiveIntegerField(default=SECTION_ORDER_DEFAULT)

    def __str__(self) -> str:
        return f"{self.course.name} – {self.title}"


# ======================= LESSON ======================= #
class LessonKind(models.TextChoices):
    VIDEO = "VIDEO", _("Video")
    NOTE = "NOTE", _("Ghi chú")
    QUIZ = "QUIZ", _("Bài kiểm tra")


class Lesson(models.Model):
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name=_("Course"),
    )
    section = models.ForeignKey(
        "courses.Section",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lessons",
        verbose_name=_("Section"),
        help_text=_("Chọn phần cho bài học (ví dụ: Từ vựng, Ngữ pháp, Luyện đề, ...)")
    )
    title = models.CharField(_("Lesson Title"), max_length=LESSON_TITLE_MAX_LENGTH)
    description = models.TextField(_("Description"), blank=True)
    order = models.PositiveIntegerField(_("Order"), default=LESSON_ORDER_DEFAULT)

    video_url = models.URLField(_("Video URL"), blank=True, null=True)
    video_file = models.FileField(
        _("Video File"),
        upload_to=LESSON_VIDEO_UPLOAD_PATH,
        blank=True,
        null=True,
    )
    duration_minutes = models.PositiveIntegerField(
        _("Video Duration (minutes)"),
        default=0,
        help_text=_("Thời lượng video bài học (phút)"),
    )

    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Lesson")
        verbose_name_plural = _("Lessons")
        ordering = LESSON_DEFAULT_ORDERING
        unique_together = (LESSON_UNIQUE_TOGETHER,)

    def __str__(self) -> str:
        return f"{self.course.name} – {self.title}"

    def clean(self):
        if not self.video_url and not self.video_file:
            raise ValidationError({"video_url": _(LESSON_VIDEO_REQUIRED_MSG)})

    # ---------- Duration helpers ----------
    @property
    def video_duration_minutes(self):
        if self.duration_minutes:
            return int(self.duration_minutes)
        if self.video_url and "youtube.com" in self.video_url:
            try:
                from .utils_youtube import get_youtube_video_duration_minutes
                return get_youtube_video_duration_minutes(self.video_url) or 0
            except Exception:
                return 0
        return 0

    @property
    def test_duration_minutes(self):
        if hasattr(self, "quiz") and self.quiz and self.quiz.time_minutes:
            return int(self.quiz.time_minutes)
        return 0

    @property
    def total_duration_minutes(self):
        return self.video_duration_minutes + self.test_duration_minutes

    @property
    def total_duration_text(self):
        return f"{self.total_duration_minutes} phút" if self.total_duration_minutes > 0 else ""


# ======================= ENROLLMENT ======================= #
class EnrollmentStatus(models.TextChoices):
    PENDING = "PENDING", _("Chờ duyệt")
    APPROVED = "APPROVED", _("Đã duyệt")
    REJECTED = "REJECTED", _("Từ chối")


class Enrollment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name=_("User"),
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name=_("Course"),
    )
    status = models.CharField(
        _("Status"),
        max_length=MAX_STATUS_LENGTH,
        choices=STATUS_CHOICES,
        default=EnrollmentStatus.PENDING.value,
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    approved_at = models.DateTimeField(_("Approved at"), null=True, blank=True)

    class Meta:
        verbose_name = _("Enrollment")
        verbose_name_plural = _("Enrollments")
        unique_together = ("user", "course")

    def __str__(self):
        return f"{self.user} → {self.course} [{self.status}]"


@receiver(post_save, sender=Enrollment)
def enrollment_status_notification(sender, instance, created, **kwargs):
    from notifications.services import send_notification

    if created:
        send_notification(
            instance.user,
            _("Bạn đã đăng ký khóa học '%(course)s' thành công. Vui lòng chờ xét duyệt.")
            % {"course": instance.course.name},
        )
    else:
        old = Enrollment.objects.filter(pk=instance.pk).first()
        if old and old.status != instance.status:
            if instance.status == EnrollmentStatus.APPROVED.value:
                send_notification(
                    instance.user,
                    _("Bạn đã được duyệt vào khóa học '%(course)s'. Hãy bắt đầu học ngay!")
                    % {"course": instance.course.name},
                )
            elif instance.status == EnrollmentStatus.REJECTED.value:
                send_notification(
                    instance.user,
                    _("Bạn đã bị từ chối vào khóa học '%(course)s'. Vui lòng liên hệ admin để biết thêm chi tiết.")
                    % {"course": instance.course.name},
                )


# ======================= REVIEW ======================= #
class CourseReview(models.Model):
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("Course"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="course_reviews",
        verbose_name=_("User"),
    )
    rating = models.PositiveSmallIntegerField(
        _("Rating"),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_("Số sao (1-5)"),
    )
    comment = models.TextField(_("Comment"), blank=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Course Review")
        verbose_name_plural = _("Course Reviews")
        unique_together = ("course", "user")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.course} ({self.rating}★)"

    @staticmethod
    def get_avg_rating(course):
        from django.db.models import Avg
        return course.reviews.aggregate(avg=Avg("rating"))["avg"] or 0


# ======================= TEACHER ======================= #
class Teacher(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Tên giảng viên"))
    bio = models.TextField(verbose_name=_("Giới thiệu"), blank=True)
    avatar = models.ImageField(
        upload_to="teachers/avatars/",
        blank=True,
        null=True,
        verbose_name=_("Ảnh đại diện"),
    )
    position = models.TextField(blank=True, verbose_name=_("Chức danh"))
    experience = models.TextField(blank=True, verbose_name=_("Kinh nghiệm"))

    def __str__(self):
        return self.name
