import nested_admin
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Quiz, Question, Choice

class ChoiceInline(nested_admin.NestedTabularInline):
    model = Choice
    extra = 4
    fields = ('text', 'is_correct')
    # nếu muốn ẩn cột is_correct trong form add thì cho thêm readonly_fields…

class QuestionInline(nested_admin.NestedStackedInline):
    model = Question
    extra = 1
    fields = ('order', 'text', 'explanation')
    inlines = [ChoiceInline]    # ← lồng inline Choice vào Question

@admin.register(Quiz)
class QuizAdmin(nested_admin.NestedModelAdmin):
    list_display = ('title', 'lesson', 'time_minutes', 'pass_rate', 'question_count')
    list_filter  = ('lesson__course',)
    search_fields = ('title',)
    inlines = [QuestionInline]  # ← chỉ cần QuizInline có nested Question + Choice

    def question_count(self, obj):
        return obj.question_count
    question_count.short_description = _("Number of Questions")
