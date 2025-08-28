# admin.py

import nested_admin
from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Quiz, Question, Choice


# ----- Forms -----
class QuizAdminForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        errors = []

        time_minutes = cleaned_data.get("time_minutes")
        pass_rate = cleaned_data.get("pass_rate")

        # 1) Thời lượng quiz > 2 phút
        if time_minutes is not None and time_minutes <= 2:
            errors.append(_("Thời lượng quiz phải lớn hơn 2 phút."))

        # 2) Tỷ lệ pass > 50%
        if pass_rate is not None and pass_rate <= 50:
            errors.append(_("Tỷ lệ pass phải lớn hơn 50%."))

        # 3) Phải có ít nhất 1 câu hỏi (khi đã có instance)
        instance = self.instance
        questions = instance.questions.all() if instance and instance.pk else []

        if not questions or questions.count() == 0:
            errors.append(_("Quiz phải có ít nhất 1 câu hỏi."))

        # 4) Mỗi câu hỏi phải có ít nhất 1 lựa chọn và có đáp án đúng
        for q in questions:
            choices = q.choices.all()
            if choices.count() == 0:
                errors.append(_('Câu hỏi "%(q)s" phải có ít nhất 1 câu trả lời.') % {"q": q.text})
            elif not choices.filter(is_correct=True).exists():
                errors.append(_('Câu hỏi "%(q)s" phải có ít nhất 1 đáp án đúng.') % {"q": q.text})

        if errors:
            raise ValidationError(errors)
        return cleaned_data


# ----- Inlines -----
class ChoiceInline(nested_admin.NestedTabularInline):
    model = Choice
    extra = 4
    fields = ("text", "is_correct")


class QuestionInline(nested_admin.NestedStackedInline):
    model = Question
    extra = 1
    fields = ("order", "text", "explanation")
    inlines = [ChoiceInline]  # Lồng Choice vào Question


# ----- Admins -----
@admin.register(Quiz)
class QuizAdmin(nested_admin.NestedModelAdmin):
    form = QuizAdminForm
    list_display = ("title", "lesson", "time_minutes", "pass_rate", "question_count")
    list_filter = ("lesson__course",)
    search_fields = ("title",)
    inlines = [QuestionInline]

    def question_count(self, obj):
        return obj.question_count

    question_count.short_description = _("Number of Questions")
