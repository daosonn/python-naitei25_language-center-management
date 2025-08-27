# views.py
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from constants import PROGRESS_DONUT_CIRCUMFERENCE

from courses.models import Course, Lesson
from .models import LessonProgress


@login_required
@require_POST
def mark_lesson_complete(request, lesson_id):
    """
    Đánh dấu 1 bài học đã hoàn thành cho user hiện tại và lưu snapshot.
    Trả về JSON: {success: bool, created: bool}
    """
    lesson = get_object_or_404(Lesson, pk=lesson_id)

    snapshot = {
        "title": lesson.title,
        "description": lesson.description,
        "order": lesson.order,
        "video_url": lesson.video_url,
        "video_file": lesson.video_file.url if lesson.video_file else None,
        "course": {
            "id": lesson.course.id,
            "name": lesson.course.name,
        },
    }

    _, created = LessonProgress.objects.update_or_create(
        user=request.user,
        lesson=lesson,
        defaults={"snapshot": snapshot},
    )

    return JsonResponse({"success": True, "created": created})


class CourseProgressView(LoginRequiredMixin, TemplateView):
    """
    Hiển thị tiến độ học của người dùng:
    - Danh sách tiến độ theo từng khóa (progress bar + %)
    - Tổng tiến độ (donut chart)
    - Có thể lọc theo 1 khóa học cụ thể qua ?course=<id>
    """
    template_name = "user_progress/course_progress.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Tập khóa học có liên quan: đã enroll hoặc đã có progress
        enrolled_courses = Course.objects.filter(enrollments__user=user).distinct()
        progress_courses = Course.objects.filter(lessons__progresses__user=user).distinct()
        courses = (enrolled_courses | progress_courses).distinct()

        selected_course_id = self.request.GET.get("course")

        progress_list = []
        for course in courses:
            total = course.lessons.count()
            completed = LessonProgress.objects.filter(
                user=user, lesson__course=course
            ).count()
            percent = int((completed / total) * 100) if total else 0

            progress_list.append(
                {
                    "id": course.id,
                    "title": course.name,
                    "completed": completed,
                    "total": total,
                    "percent": percent,
                }
            )

        # Tổng hợp theo lựa chọn hoặc toàn bộ
        if selected_course_id:
            selected = next((c for c in progress_list if str(c["id"]) == str(selected_course_id)), None)
            if selected:
                total_lessons = selected["total"]
                total_completed = selected["completed"]
                overall_percent = selected["percent"]
            else:
                total_lessons = 0
                total_completed = 0
                overall_percent = 0
        else:
            total_lessons = sum(c["total"] for c in progress_list)
            total_completed = sum(c["completed"] for c in progress_list)
            overall_percent = int((total_completed / total_lessons) * 100) if total_lessons else 0

        # Donut chart: tính offset từ chu vi và % hoàn thành (không hardcode 3.77)
        stroke_dashoffset = PROGRESS_DONUT_CIRCUMFERENCE * (1 - overall_percent / 100.0)

        context.update(
            {
                "progress_list": progress_list,
                "overall_percent": overall_percent,
                "total_completed": total_completed,
                "total_lessons": total_lessons,
                "stroke_dashoffset": stroke_dashoffset,
                "selected_course_id": selected_course_id,
                "donut_circumference": PROGRESS_DONUT_CIRCUMFERENCE,
            }
        )
        return context
