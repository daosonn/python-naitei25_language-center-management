from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe

register = template.Library()

# ---------- Helpers ----------
def _state_from_review(r):
    """
    r: phần tử trong 'review' context (có thuộc tính: is_skip, is_correct, is_wrong, user_choice_obj, question)
    return: 'skip' | 'correct' | 'wrong'
    """
    if getattr(r, "is_skip", False):
        return "skip"
    if getattr(r, "is_correct", False):
        return "correct"
    return "wrong"


# ---------- Simple tag: icon theo trạng thái ----------
@register.simple_tag
def state_icon(state: str, size: str = "lg"):
    """
    Render biểu tượng dựa trên state với lớp CSS:
    .qi-icon .qi-{state} .qi-{size}; CSS đã định nghĩa trong courses/static/courses/css/quiz.css
    """
    cls = f"qi-icon qi-{state} qi-{size}"
    return mark_safe(f'<span class="{cls}" aria-hidden="true"></span>')


# ---------- Inclusion tags ----------
@register.inclusion_tag("quizzes/partials/review_header.html")
def review_header(r, idx: int):
    """Header accordion của từng câu."""
    return {"state": _state_from_review(r), "r": r, "idx": idx}

@register.inclusion_tag("quizzes/partials/review_badge.html")
def review_badge(r):
    """Badge: Đúng/Sai/Bỏ qua."""
    return {"state": _state_from_review(r)}

@register.inclusion_tag("quizzes/partials/review_choice_list.html")
def review_choice_list(r):
    """Danh sách lựa chọn với tick/cross chỉ ở đáp án user đã chọn."""
    return {"r": r}

@register.inclusion_tag("quizzes/partials/review_all_choices.html")
def review_all_choices(r):
    """Danh sách toàn bộ lựa chọn: tick xanh cho đáp án đúng, X đỏ ở lựa chọn user đã chọn (nếu sai)."""
    return {"r": r}

@register.inclusion_tag("quizzes/partials/back_to_lesson.html")
def back_to_lesson(quiz):
    """
    Nút 'Quay lại bài học' — tự động chọn route theo slug hoặc id.
    Nếu dự án bạn dùng tên route khác cho path theo id, sửa lại bên dưới cho đúng.
    """
    course = quiz.lesson.course
    lesson = quiz.lesson
    slug = getattr(course, "slug", None)
    if slug:
        url = reverse("courses:lesson", args=[slug, lesson.id])
    else:
        # Đổi 'courses:lesson_by_id' nếu project đặt tên khác
        url = reverse("courses:lesson_by_id", args=[course.id, lesson.id])
    return {"url": url}
