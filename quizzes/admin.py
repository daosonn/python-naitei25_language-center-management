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

        # 2) Tỷ lệ pass > 0 và <= 100
        if pass_rate is not None and (pass_rate <= 0 or pass_rate > 100):
            errors.append(_("Tỷ lệ pass phải lớn hơn 0% và nhỏ hơn hoặc bằng 100%."))


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
