# quizzes/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from .forms import QuizForm
from .models import Choice, Quiz


@login_required
def quiz_detail(request, lesson_id: int):
    """
    - GET: hiển thị form quiz
    - POST: chấm điểm, trả score/passed + dữ liệu review/results cho template
    - Tối ưu N+1 với select_related/prefetch_related
    """
    quiz = get_object_or_404(
        Quiz.objects.select_related("lesson__course")
        .prefetch_related("questions__choices"),
        lesson__id=lesson_id,
    )
    course_id = quiz.lesson.course_id
    questions = list(quiz.questions.all())

    if request.method == "POST":
        form = QuizForm(request.POST, quiz=quiz)
        if form.is_valid():
            total_q = len(questions)
            correct = 0

            review = []   # cho template mới (quizzes/result.html)
            results = []  # giữ tương thích template cũ (quizzes/quiz_result.html)


            for q in questions:
                field = f"question_{q.pk}"
                sel_raw = form.cleaned_data.get(field)

                selected = None
                if sel_raw not in (None, ""):
                    try:
                        sel_id = int(sel_raw)
                        selected = q.choices.get(pk=sel_id)
                    except (ValueError, Choice.DoesNotExist):
                        selected = None

                correct_choice = None
                for ch in q.choices.all():
                    if ch.is_correct:
                        correct_choice = ch
                        break

                is_correct = bool(selected and selected.is_correct)
                is_skip = selected is None
                is_wrong = (selected is not None and not is_correct)
                if is_correct:
                    correct += 1

                review.append({
                    "question": q,  # truyền object để lấy giải thích và choices
                    "user_choice": selected.text if selected else "—",
                    "user_choice_obj": selected,
                    "correct_choice": correct_choice.text if correct_choice else "—",
                    "correct_choice_obj": correct_choice,
                    "is_correct": is_correct,
                    "is_wrong": is_wrong,
                    "is_skip": is_skip,
                })

                results.append({
                    "question": q,
                    "selected": selected,
                    "is_correct": is_correct,
                    "correct_choice": correct_choice,
                })

            score = round((correct / total_q) * 100, 2) if total_q else 0.0
            passed = (score >= quiz.pass_rate) if total_q else False

            # 👉 Nếu bạn đang dùng template cũ, đổi 'quizzes/result.html' thành 'quizzes/quiz_result.html'
            return render(
                request,
                "quizzes/result.html",
                {
                    "quiz": quiz,
                    "score": score,
                    "passed": passed,
                    "review": review,
                    "results": results,
                    "course_id": course_id,
                },
            )
    else:
        form = QuizForm(quiz=quiz)

    # GET
    return render(
        request,
        "quizzes/detail.html",
        {
            "quiz": quiz,
            "form": form,
            "questions": questions,  # nếu template muốn duyệt trực tiếp
            "course_id": course_id,
        },
    )
