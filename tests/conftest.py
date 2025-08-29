# tests/conftest.py
import pytest
from django.contrib.auth import get_user_model
from courses.models import Teacher, Course, Lesson
from quizzes.models import Quiz, Question, Choice

@pytest.fixture
def user_password():
    return "S0n_Test_123"

@pytest.fixture
def user(db, user_password):
    User = get_user_model()
    return User.objects.create_user(
        email="son@example.com", username="son@example.com", password=user_password
    )

@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client

@pytest.fixture
def course(db):
    t = Teacher.objects.create(name="Sensei")
    return Course.objects.create(name="N5 Mastery", teacher=t)

@pytest.fixture
def lesson(db, course):
    return Lesson.objects.create(course=course, title="Kana 101")

@pytest.fixture
def quiz(db, lesson):
    # 👇 thêm time_minutes để tránh NOT NULL
    qz = Quiz.objects.create(
        lesson=lesson, title="Quick quiz", time_minutes=5, pass_rate=50
    )
    q1 = Question.objects.create(quiz=qz, text="Hiragana 'a' ?", order=1)
    Choice.objects.bulk_create([
        Choice(question=q1, text="あ", is_correct=True),
        Choice(question=q1, text="い", is_correct=False),
    ])
    return qz
