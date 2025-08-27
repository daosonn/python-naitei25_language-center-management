from __future__ import annotations

# ===== Stdlib =====
import re
from urllib.parse import urlparse, parse_qs

# ===== Django core / contrib =====
from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Q, Avg, Count, Prefetch
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import (
    TemplateView, ListView, CreateView, UpdateView, DeleteView, DetailView, FormView
)

# ===== Project constants =====
from core import constants as C  # có thể không có, nên có fallback
from constants import (
    # Query params & sort
    COURSE_QUERY_PARAM,
    COURSE_SORT_PARAM,
    COURSE_SORT_POPULAR,
    COURSE_SORT_RATING,
    COURSE_SORT_NEW,
    COURSE_ORDER_BY_POPULAR,
    COURSE_ORDER_BY_RATING,
    COURSE_ORDER_BY_NEW,
    MY_COURSES_PAGE_SIZE,

    # Fallback & embed
    COURSE_LIST_PAGE_SIZE,
    LESSON_ORDERING_FALLBACK,
    LESSON_ORDERING_WITH_SECTION,
    YOUTUBE_EMBED_BASE,

    # Messages
    ENROLL_SUCCESS_MSG,
    ENROLL_ALREADY_APPROVED_MSG,
    COURSE_NO_LESSON_MSG,
    COURSE_NEED_APPROVAL_MSG,

    # Enum/hằng khác
    EnrollmentStatus,
)

# ===== Local apps =====
from .forms import LessonForm, CourseForm  # (CourseForm có thể dùng ở nơi khác)
from .mixins import CourseAccessRequiredMixin
from .models import Course, Lesson, Enrollment, CourseReview
from .utils import _extract_youtube_id, user_can_access_course

from user_progress.models import LessonProgress
from quizzes.models import Quiz, Question, Choice, Submission, Answer


# =====================================================
# Helpers
# =====================================================
def _model_has_field(model, field_name: str) -> bool:
    """Kiểm tra model có field hay không (an toàn khi cấu hình thay đổi)."""
    try:
        model._meta.get_field(field_name)
        return True
    except FieldDoesNotExist:
        return False


HAS_LESSON_SECTION = _model_has_field(Lesson, "section")


# =====================================================
# Home
# =====================================================
class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        courses = Course.objects.annotate(
            avg_rating=Avg("reviews__rating"),
            num_reviews=Count("reviews"),
            num_students=Count("enrollments", filter=Q(enrollments__status=EnrollmentStatus.APPROVED.value)),
        ).order_by("-avg_rating", "-num_reviews", "-num_students")[:4]
        context["courses"] = courses
        return context


# =====================================================
# Course: List / Detail
# =====================================================
class CourseListView(LoginRequiredMixin, ListView):
    """
    Danh sách khoá học (grid) + search, sort, paginate.
    """
    model = Course
    template_name = "courses/course_list.html"
    context_object_name = "courses"
    paginate_by = C.PAGINATION.get("COURSE_LIST_PAGE_SIZE", COURSE_LIST_PAGE_SIZE) if hasattr(C, "PAGINATION") else COURSE_LIST_PAGE_SIZE

    def get_queryset(self):
        qs = Course.objects.all().order_by("-id")

        q = self.request.GET.get(COURSE_QUERY_PARAM)
        if q:
            qs = qs.filter(name__icontains=q)

        sort = self.request.GET.get(COURSE_SORT_PARAM)
        if sort == COURSE_SORT_POPULAR:
            qs = qs.order_by(*COURSE_ORDER_BY_POPULAR)
        elif sort == COURSE_SORT_RATING:
            qs = qs.order_by(*COURSE_ORDER_BY_RATING)
        elif sort == COURSE_SORT_NEW:
            qs = qs.order_by(*COURSE_ORDER_BY_NEW)

        return qs.prefetch_related("enrollments")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["query"] = self.request.GET.get(COURSE_QUERY_PARAM, "")
        ctx["sort"] = self.request.GET.get(COURSE_SORT_PARAM, "")
        # annotate nhẹ nhàng cho UI
        for course in ctx.get("courses", []):
            reviews = CourseReview.objects.filter(course=course)
            ratings = [r.rating for r in reviews]
            course.rating_count = len(ratings)
            course.rating_avg = round(sum(ratings) / len(ratings), 2) if ratings else 0.0
            course.students_count = course.enrollments.filter(status=EnrollmentStatus.APPROVED.value).count()
        return ctx


class CourseDetailView(DetailView):
    model = Course
    template_name = "courses/course_detail.html"
    context_object_name = "course"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    pk_url_kwarg = "pk"

    def get_object(self, queryset=None):
        qs = queryset or super().get_queryset()
        slug = self.kwargs.get(self.slug_url_kwarg)
        if slug:
            return get_object_or_404(qs, **{self.slug_field: slug})
        pk = self.kwargs.get(self.pk_url_kwarg) or self.kwargs.get("id") or self.kwargs.get("course_id")
        return get_object_or_404(qs, pk=pk)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        course = self.object

        # Lessons ordering
        lessons_qs = Lesson.objects.filter(course=course)
        if HAS_LESSON_SECTION:
            lessons_qs = lessons_qs.select_related("section")
            ordering = LESSON_ORDERING_WITH_SECTION
        else:
            ordering = LESSON_ORDERING_FALLBACK
        ctx["lessons"] = lessons_qs.order_by(*ordering)

        # Enrollment
        user = self.request.user
        enrollment = None
        if user.is_authenticated:
            enrollment = Enrollment.objects.filter(user=user, course=course).only("id", "status", "approved_at").first()
        ctx["enrollment"] = enrollment
        ctx["user_is_enrolled"] = (
            bool(enrollment and enrollment.status == EnrollmentStatus.APPROVED.value)
            or (user.is_authenticated and (user.is_staff or user.is_superuser))
        )

        # Reviews
        ctx["reviews"] = CourseReview.objects.filter(course=course).select_related("user").order_by("-created_at")
        ctx["avg_rating"] = CourseReview.get_avg_rating(course)
        ctx["review_form"] = CourseReviewForm()
        return ctx


class MyCoursesView(LoginRequiredMixin, ListView):
    model = Course
    template_name = "courses/my_courses.html"
    context_object_name = "courses"
    paginate_by = (
        C.PAGINATION.get("MY_COURSES_PAGE_SIZE", MY_COURSES_PAGE_SIZE)
        if hasattr(C, "PAGINATION")
        else MY_COURSES_PAGE_SIZE
    )

    def get_queryset(self):
        user = self.request.user

        # Chỉ lấy các enrollment đã duyệt của user
        approved_enr_qs = (
            Enrollment.objects
            .filter(user=user, status=EnrollmentStatus.APPROVED.value)
            .only("id", "course_id", "approved_at", "status")
        )

        return (
            Course.objects
            .filter(enrollments__in=approved_enr_qs)
            .prefetch_related(
                Prefetch("enrollments", queryset=approved_enr_qs, to_attr="my_enrollments"),
                "lessons"  # nếu Lesson có related_name='lessons'
            )
            .distinct()
            .order_by("-enrollments__approved_at", "-id")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = _("Khóa học của tôi")
        return ctx


# =====================================================
# Lesson: List / CRUD / Detail (đơn)
# =====================================================
class LessonListView(LoginRequiredMixin, ListView):
    model = Lesson
    template_name = "courses/lesson_list.html"
    context_object_name = "lessons"

    def get_queryset(self):
        self.course = get_object_or_404(Course, id=self.kwargs["course_id"])
        return Lesson.objects.filter(course=self.course).select_related("course").order_by(*LESSON_ORDERING_FALLBACK)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["course"] = self.course
        completed_ids = LessonProgress.objects.filter(
            user=self.request.user, lesson__in=data["lessons"]
        ).values_list("lesson_id", flat=True)
        data["completed_lessons"] = set(completed_ids)
        return data


class LessonCreateView(LoginRequiredMixin, CreateView):
    model = Lesson
    form_class = LessonForm
    template_name = "courses/lesson_form.html"

    def get_initial(self):
        return {"course": get_object_or_404(Course, id=self.kwargs["course_id"])}

    def form_valid(self, form):
        form.instance.course = get_object_or_404(Course, id=self.kwargs["course_id"])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("courses:lesson_list", kwargs={"course_id": self.kwargs["course_id"]})


class LessonUpdateView(LoginRequiredMixin, UpdateView):
    model = Lesson
    form_class = LessonForm
    template_name = "courses/lesson_form.html"

    def get_success_url(self):
        return reverse_lazy("courses:lesson_list", kwargs={"course_id": self.object.course.id})


class LessonDeleteView(LoginRequiredMixin, DeleteView):
    model = Lesson

    def get_success_url(self):
        return reverse_lazy("courses:lesson_list", kwargs={"course_id": self.object.course.id})

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        course_id = self.object.course.id
        self.object.delete()
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True, "course_id": course_id})
        return HttpResponseRedirect(self.get_success_url())


class LessonDetailView(LoginRequiredMixin, DetailView):
    model = Lesson
    template_name = "courses/lesson_detail.html"
    context_object_name = "lesson"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        lesson = data["lesson"]

        embed_url = ""
        if getattr(lesson, "video_url", None):
            vid = _extract_youtube_id(lesson.video_url)
            if vid:
                embed_url = f"{YOUTUBE_EMBED_BASE}{vid}"

        data["embed_url"] = embed_url
        data["has_quiz"] = hasattr(lesson, "quiz")
        return data


# =====================================================
# Lesson Learn (layout với playlist + prev/next)
# =====================================================
class LessonLearnView(CourseAccessRequiredMixin, DetailView):
    """
    Yêu cầu URL có 'slug' HOẶC 'course_id' (fallback lesson_id → suy ngược course_id).
    """
    model = Lesson
    pk_url_kwarg = "lesson_id"
    template_name = "courses/lesson_learn.html"

    def get_queryset(self):
        qs = Lesson.objects.select_related("course")
        slug = self.kwargs.get("slug")

        if slug:
            try:
                Course._meta.get_field("slug")
                return qs.filter(course__slug=slug)
            except Exception:
                pass

        course_id = self.kwargs.get("course_id")
        if course_id:
            return qs.filter(course_id=course_id)

        lesson_id = self.kwargs.get("lesson_id")
        if lesson_id:
            try:
                course_id = Lesson.objects.only("course_id").get(pk=lesson_id).course_id
                return qs.filter(course_id=course_id)
            except Lesson.DoesNotExist:
                return qs.none()

        return qs.none()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        lesson = self.object
        user = self.request.user

        # Playlist
        try:
            siblings = list(
                lesson.course.lessons.select_related("course").order_by(*LESSON_ORDERING_WITH_SECTION)
            )
        except Exception:
            siblings = list(
                lesson.course.lessons.select_related("course").order_by(*LESSON_ORDERING_FALLBACK)
            )

        # Completed lessons
        completed_ids = set(
            LessonProgress.objects.filter(user=user, lesson__in=siblings).values_list("lesson_id", flat=True)
        )

        # Quiz passed dict
        quiz_passed = {}
        for l in siblings:
            if hasattr(l, "quiz") and l.quiz:
                sub = (
                    Submission.objects.filter(user=user, quiz=l.quiz, submitted_at__isnull=False)
                    .order_by("-submitted_at")
                    .first()
                )
                if sub and l.quiz.pass_rate:
                    total = l.quiz.question_count
                    if total > 0:
                        percent = (sub.correct_cnt / total) * 100
                        quiz_passed[l.id] = percent >= l.quiz.pass_rate
                    else:
                        quiz_passed[l.id] = False
                else:
                    quiz_passed[l.id] = False
            else:
                quiz_passed[l.id] = None  # Không có quiz

        # Prev/Next
        idx = next((i for i, x in enumerate(siblings) if x.id == lesson.id), 0)
        prev_lesson = siblings[idx - 1] if idx > 0 else None
        next_lesson = siblings[idx + 1] if idx < len(siblings) - 1 else None

        # Embed URL
        embed_url = ""
        if getattr(lesson, "video_url", None):
            vid = _extract_youtube_id(lesson.video_url)
            if vid:
                embed_url = f"{YOUTUBE_EMBED_BASE}{vid}"

        ctx.update({
            "siblings": siblings,
            "completed_lessons": completed_ids,
            "quiz_passed": quiz_passed,
            "prev_lesson": prev_lesson,
            "next_lesson": next_lesson,
            "embed_url": embed_url,
        })
        return ctx


# =====================================================
# Quiz: start → take → result
# =====================================================
class QuizStartView(CourseAccessRequiredMixin, View):
    template_name = "courses/quiz_start.html"

    def get(self, request, **kwargs):
        lesson_id = kwargs["lesson_id"]
        slug = kwargs.get("slug")
        if slug:
            try:
                lesson = get_object_or_404(Lesson, id=lesson_id, course__slug=slug)
            except Exception:
                lesson = get_object_or_404(Lesson, id=lesson_id)
        else:
            course_id = kwargs.get("course_id")
            if course_id:
                lesson = get_object_or_404(Lesson, id=lesson_id, course_id=course_id)
            else:
                lesson = get_object_or_404(Lesson, id=lesson_id)

        quiz = get_object_or_404(Quiz, lesson=lesson)
        return render(
            request,
            self.template_name,
            {"lesson": lesson, "quiz": quiz, "course": getattr(self, "course", lesson.course)},
        )

    def post(self, request, **kwargs):
        lesson = get_object_or_404(Lesson, id=kwargs["lesson_id"])
        quiz = get_object_or_404(Quiz, lesson=lesson)
        sub = Submission.objects.create(quiz=quiz, user=request.user)
        if "slug" in kwargs:
            return redirect("courses:quiz_take", slug=kwargs["slug"], submission_id=sub.id)
        course_id = kwargs.get("course_id")
        if course_id:
            return redirect("courses:quiz_take_by_id", course_id=course_id, submission_id=sub.id)
        return redirect("courses:quiz_take", slug=getattr(lesson.course, "slug", ""), submission_id=sub.id)


class QuizTakeView(CourseAccessRequiredMixin, View):
    template_name = "courses/quiz_take.html"

    def get(self, request, **kwargs):
        sub = get_object_or_404(
            Submission.objects.select_related("quiz__lesson__course"),
            id=kwargs["submission_id"],
            user=request.user,
        )
        quiz = sub.quiz
        end_at = sub.started_at + timezone.timedelta(minutes=quiz.time_minutes)
        questions = quiz.questions.prefetch_related("choices").order_by("order", "id")
        return render(
            request,
            self.template_name,
            {
                "submission": sub,
                "quiz": quiz,
                "questions": questions,
                "end_at": int(end_at.timestamp() * 1000),
            },
        )

    def post(self, request, **kwargs):
        sub = get_object_or_404(Submission, id=kwargs["submission_id"], user=request.user)
        quiz = sub.quiz
        correct = wrong = skip = 0
        for q in quiz.questions.all():
            choice_id = request.POST.get(f"q{q.id}")
            if not choice_id:
                skip += 1
                Answer.objects.create(submission=sub, question=q, choice=None)
                continue
            ch = Choice.objects.filter(id=choice_id, question=q).first()
            Answer.objects.create(submission=sub, question=q, choice=ch)
            if ch and ch.is_correct:
                correct += 1
            else:
                wrong += 1
        sub.correct_cnt = correct
        sub.wrong_cnt = wrong
        sub.skip_cnt = skip
        sub.score = correct
        sub.submitted_at = timezone.now()
        sub.save()

        if "slug" in kwargs:
            return redirect("courses:quiz_result", slug=kwargs["slug"], submission_id=sub.id)
        course_id = kwargs.get("course_id")
        if course_id:
            return redirect("courses:quiz_result_by_id", course_id=course_id, submission_id=sub.id)
        return redirect("courses:quiz_result", slug=getattr(sub.quiz.lesson.course, "slug", ""), submission_id=sub.id)


class QuizResultView(CourseAccessRequiredMixin, DetailView):
    model = Submission
    pk_url_kwarg = "submission_id"
    template_name = "courses/quiz_result.html"

    def get_queryset(self):
        return Submission.objects.select_related("quiz__lesson__course").filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        sub = self.object
        duration_seconds = 0
        if sub.submitted_at and sub.started_at:
            duration_seconds = int((sub.submitted_at - sub.started_at).total_seconds())
        m, s = divmod(duration_seconds, 60)
        ctx["duration_seconds"] = duration_seconds
        ctx["duration_text"] = f"{m} phút {s} giây" if m else f"{s} giây"
        ctx["answers"] = sub.answers.select_related("question", "choice").all()
        return ctx


# =====================================================
# Review: Form / List / Submit
# =====================================================
class CourseReviewForm(forms.ModelForm):
    class Meta:
        model = CourseReview
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5, "type": "number", "class": "form-control"}),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class CourseReviewListView(ListView):
    model = CourseReview
    template_name = "courses/course_review_list.html"
    context_object_name = "reviews"

    def get_queryset(self):
        course_id = self.kwargs["course_id"]
        return CourseReview.objects.filter(course_id=course_id).select_related("user").order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = self.kwargs["course_id"]
        context["course"] = Course.objects.get(pk=course_id)
        context["avg_rating"] = CourseReview.get_avg_rating(context["course"])
        context["form"] = CourseReviewForm()
        return context


class CourseReviewSubmitView(LoginRequiredMixin, FormView):
    form_class = CourseReviewForm
    template_name = "courses/course_review_submit.html"  # không render trực tiếp

    def form_valid(self, form):
        course_id = self.kwargs["course_id"]
        course = Course.objects.get(pk=course_id)
        CourseReview.objects.update_or_create(
            course=course, user=self.request.user,
            defaults={"rating": form.cleaned_data["rating"], "comment": form.cleaned_data["comment"]},
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("courses:review_list", kwargs={"course_id": self.kwargs["course_id"]})

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        # Nếu lỗi, quay lại trang review list với form lỗi
        course_id = self.kwargs["course_id"]
        course = Course.objects.get(pk=course_id)
        reviews = CourseReview.objects.filter(course=course).order_by("-created_at")
        avg_rating = CourseReview.get_avg_rating(course)
        return self.render_to_response(self.get_context_data(form=form, reviews=reviews, course=course, avg_rating=avg_rating))


# =====================================================
# Course Progress
# =====================================================
class CourseProgressView(LoginRequiredMixin, TemplateView):
    template_name = "courses/course_progress.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        course = get_object_or_404(Course, id=self.kwargs["course_id"])
        total = course.lessons.count()
        completed = LessonProgress.objects.filter(user=self.request.user, lesson__course=course).count()
        percent = int((completed / total) * 100) if total else 0
        ctx.update({
            "course": course,
            "total_lessons": total,
            "completed_lessons": completed,
            "percent": percent,
        })
        return ctx


# =====================================================
# Enrollment: request/approve + start course
# =====================================================
@login_required
@require_POST
def enroll_request_id(request, pk):
    course = get_object_or_404(Course, pk=pk)
    enr, created = Enrollment.objects.get_or_create(
        user=request.user, course=course,
        defaults={"status": EnrollmentStatus.PENDING.value},
    )
    if not created and enr.status == EnrollmentStatus.REJECTED.value:
        enr.status = EnrollmentStatus.PENDING.value
        enr.approved_at = None
        enr.save(update_fields=["status", "approved_at"])

    if enr.status == EnrollmentStatus.APPROVED.value:
        messages.info(request, _(ENROLL_ALREADY_APPROVED_MSG))
    else:
        messages.success(request, _(ENROLL_SUCCESS_MSG))
    return redirect("courses:detail_by_id", pk=course.pk)


@login_required
@require_POST
def enroll_request_slug(request, slug):
    course = get_object_or_404(Course, slug=slug)
    enr, created = Enrollment.objects.get_or_create(
        user=request.user, course=course,
        defaults={"status": EnrollmentStatus.PENDING.value},
    )
    if not created and enr.status == EnrollmentStatus.REJECTED.value:
        enr.status = EnrollmentStatus.PENDING.value
        enr.approved_at = None
        enr.save(update_fields=["status", "approved_at"])

    if enr.status == EnrollmentStatus.APPROVED.value:
        messages.info(request, _(ENROLL_ALREADY_APPROVED_MSG))
    else:
        messages.success(request, _(ENROLL_SUCCESS_MSG))
    return redirect("courses:detail", slug=course.slug)


@staff_member_required
@require_POST
def approve_enrollment(request, enrollment_id):
    e = get_object_or_404(Enrollment, pk=enrollment_id)
    e.status = EnrollmentStatus.APPROVED.value
    e.approved_at = timezone.now()
    e.save(update_fields=["status", "approved_at"])
    from notifications.services import send_notification
    messages.success(request, _("Enrollment approved."))
    send_notification(
        e.user,
        _("Bạn đã được duyệt vào khóa học '%(course)s'. Hãy bắt đầu học ngay!") % {"course": e.course.name},
    )
    return redirect(e.course.get_absolute_url() if hasattr(e.course, "get_absolute_url") else "/")


# ===== Start course (đi tới bài học đầu tiên) =====
@login_required
def start_course_id(request, pk):
    course = get_object_or_404(Course, pk=pk)
    lessons = Lesson.objects.filter(course=course)
    order = LESSON_ORDERING_WITH_SECTION if HAS_LESSON_SECTION else LESSON_ORDERING_FALLBACK
    if HAS_LESSON_SECTION:
        lessons = lessons.select_related("section")
    first_lesson = lessons.order_by(*order).first()
    if not first_lesson:
        messages.info(request, _(COURSE_NO_LESSON_MSG))
        return redirect("courses:detail_by_id", pk=course.pk)
    if not user_can_access_course(request.user, course):
        messages.warning(request, _(COURSE_NEED_APPROVAL_MSG))
        return redirect("courses:detail_by_id", pk=course.pk)
    return redirect("courses:lesson_by_id", course_id=course.pk, lesson_id=first_lesson.pk)


@login_required
def start_course_slug(request, slug):
    course = get_object_or_404(Course, slug=slug)
    lessons = Lesson.objects.filter(course=course)
    order = LESSON_ORDERING_WITH_SECTION if HAS_LESSON_SECTION else LESSON_ORDERING_FALLBACK
    if HAS_LESSON_SECTION:
        lessons = lessons.select_related("section")
    first_lesson = lessons.order_by(*order).first()
    if not first_lesson:
        messages.info(request, _(COURSE_NO_LESSON_MSG))
        return redirect("courses:detail", slug=course.slug)
    if not user_can_access_course(request.user, course):
        messages.warning(request, _(COURSE_NEED_APPROVAL_MSG))
        return redirect("courses:detail", slug=course.slug)
    return redirect("courses:lesson", slug=course.slug, lesson_id=first_lesson.pk)


# =====================================================
# Lesson completion
# =====================================================
@login_required
@require_POST
def lesson_complete(request, lesson_id):
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    LessonProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson,
        defaults={"snapshot": {}},
    )
    return redirect(request.META.get("HTTP_REFERER", "/"))
