from django.db import models
from django.utils.translation import gettext_lazy as _
from courses.models import Lesson
from constants import (QUIZ_TITLE_MAX_LENGTH,CHOICE_TEXT_MAX_LENGTH)
from django.utils import timezone
from django.conf import settings

class Quiz(models.Model):
    lesson = models.OneToOneField(
        Lesson,
        on_delete=models.CASCADE,
        related_name='quiz',
        verbose_name=_("Lesson")
    )
    title = models.CharField(
        _("Quiz Title"),
        max_length=QUIZ_TITLE_MAX_LENGTH,
        help_text=_("Tiêu đề hiển thị cho bài kiểm tra")
    )
    time_minutes = models.PositiveIntegerField(
        _("Time Limit (minutes)"),
        help_text=_("Thời gian làm bài, tính theo phút")
    )
    pass_rate = models.PositiveIntegerField(
        _("Pass Rate (%)"),
        help_text=_("Tỉ lệ % để tính qua bài kiểm tra")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Quiz")
        verbose_name_plural = _("Quizzes")

    def __str__(self):
        return f"{self.title} ({self.lesson})"

    @property
    def question_count(self):
        return self.questions.count()


class Question(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_("Quiz")
    )
    text = models.TextField(_("Question Text"))

    order = models.PositiveIntegerField(
        _("Order"),
        default=0,
        help_text=_("Thứ tự hiển thị câu hỏi trong quiz")
    )
    explanation = models.TextField(
        _("Giải thích chi tiết"),
        blank=True,
        null=True,
        help_text=_("Giải thích chi tiết cho câu hỏi, hiển thị khi người dùng bấm 'xem giải thích chi tiết'.")
    )

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")
        ordering = ['order']

    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}…"

    @property
    def choice_count(self):
        return self.choices.count()


class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='choices',
        verbose_name=_("Question")
    )
    text = models.CharField(_("Choice Text"), max_length=CHOICE_TEXT_MAX_LENGTH)
    is_correct = models.BooleanField(_("Is Correct"), default=False)

    class Meta:
        verbose_name = _("Choice")
        verbose_name_plural = _("Choices")

    def __str__(self):
        return f"{'✔' if self.is_correct else '✖'} {self.text[:50]}"
class Submission(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="submissions"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    started_at = models.DateTimeField(default=timezone.now)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(default=0)
    correct_cnt = models.PositiveIntegerField(default=0)
    wrong_cnt = models.PositiveIntegerField(default=0)
    skip_cnt = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user} – {self.quiz} ({self.score} điểm)"


class Answer(models.Model):
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name="answers"
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )
    choice = models.ForeignKey(
        Choice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )