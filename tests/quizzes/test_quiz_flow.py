import pytest
from django.urls import reverse
from quizzes.models import Question, Choice

@pytest.mark.django_db
def test_quiz_detail_get_shows_form(auth_client, lesson, quiz):
    url = reverse("quizzes:detail", args=[lesson.id])
    resp = auth_client.get(url)
    assert resp.status_code == 200
    # Form phải hiện câu hỏi
    assert b"Hiragana" in resp.content

@pytest.mark.django_db
def test_quiz_submit_returns_result(auth_client, lesson, quiz):
    url = reverse("quizzes:detail", args=[lesson.id])

    # Lấy câu hỏi & đáp án đúng
    q = Question.objects.get(quiz=quiz)
    correct = Choice.objects.get(question=q, is_correct=True)

    data = {f"question_{q.pk}": str(correct.pk)}
    resp = auth_client.post(url, data)
    # View render 'quizzes/result.html' -> 200
    assert resp.status_code == 200
    # Kết quả có % điểm
    assert b"%" in resp.content
