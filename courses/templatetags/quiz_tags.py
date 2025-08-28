from django import template
from django.utils.safestring import mark_safe
from django.urls import reverse

register = template.Library()

# ---------- Helpers ----------
def _answer_state(answer):
    """Trả về: 'skip' | 'correct' | 'wrong'. Hỗ trợ cả object và dict."""
    # Nếu là dict
    if isinstance(answer, dict):
        choice_id = answer.get("choice_id")
        choice = answer.get("choice")
    else:
        choice_id = getattr(answer, "choice_id", None)
        choice = getattr(answer, "choice", None)
    if not choice_id:
        return "skip"
    if getattr(choice, "is_correct", False):
        return "correct"
    return "wrong"

# ---------- Simple tags ----------
@register.simple_tag
def state_icon(state: str, size: str = "lg"):
    """
    Hiển thị icon theo trạng thái.
    size: 'lg' | '2xl'
    """
    cls = f"qi-icon qi-{state} qi-{size}"
    return mark_safe(f'<span class="{cls}" aria-hidden="true"></span>')

# ---------- Inclusion tags ----------
@register.inclusion_tag("courses/partials/result_actions.html")
def result_actions(submission):
    """
    Render 2 nút: làm lại bài và quay lại bài giảng.
    """
    course = submission.quiz.lesson.course
    lesson = submission.quiz.lesson
    slug = getattr(course, "slug", None)
    if slug:
        lesson_url = reverse("courses:lesson", args=[slug, lesson.id])
        retry_url = reverse("courses:quiz_start", args=[slug, lesson.id])
    else:
        lesson_url = reverse("courses:lesson_by_id", args=[course.id, lesson.id]) if hasattr(lesson, 'id') else "#"
        retry_url = reverse("courses:quiz_start_by_id", args=[course.id, lesson.id])
    return {"lesson_url": lesson_url, "retry_url": retry_url}

@register.inclusion_tag("courses/partials/answer_badge.html")
def answer_badge(answer):
    return {"state": _answer_state(answer)}

@register.inclusion_tag("courses/partials/answer_header.html")
def render_answer_header(answer, idx: int):
    """Header cho mỗi câu trong accordion."""
    return {"state": _answer_state(answer), "answer": answer, "idx": idx}

@register.inclusion_tag("courses/partials/choice_list.html")
def render_choice_list(answer):
    """Danh sách lựa chọn với icon tại mục user đã chọn."""
    return {"answer": answer}

@register.inclusion_tag("courses/partials/all_choices.html")
def render_all_choices(answer):
    """Danh sách tất cả lựa chọn với tick xanh cho đáp án đúng, X đỏ cho lựa chọn sai của user."""
    return {"answer": answer}

# ---------- Filters (nếu muốn dùng ở nơi khác) ----------
@register.filter
def answer_state(answer):
    return _answer_state(answer)
