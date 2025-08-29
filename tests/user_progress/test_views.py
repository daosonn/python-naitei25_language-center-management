import pytest
from django.urls import reverse
from user_progress.models import LessonProgress
from courses.models import Course, Lesson

@pytest.mark.django_db
def test_course_progress_view_authenticated(auth_client, user, course, lesson):
    # Enroll user in course so it appears in progress view
    course.enrollments.create(user=user, status="approved")
    LessonProgress.objects.create(user=user, lesson=lesson, snapshot={"title": lesson.title})
    url = reverse("user_progress:progress")
    resp = auth_client.get(url)
    assert resp.status_code == 200
    assert "Tiến độ học tập" in resp.content.decode("utf-8")
    assert course.name in resp.content.decode("utf-8")

@pytest.mark.django_db
def test_course_progress_view_filter_course(auth_client, user, course, lesson):
    course.enrollments.create(user=user, status="approved")
    LessonProgress.objects.create(user=user, lesson=lesson, snapshot={"title": lesson.title})
    url = reverse("user_progress:progress") + f"?course={course.id}"
    resp = auth_client.get(url)
    assert resp.status_code == 200
    assert course.name in resp.content.decode("utf-8")

@pytest.mark.django_db
def test_course_progress_view_no_courses(auth_client):
    url = reverse("user_progress:progress")
    resp = auth_client.get(url)
    assert resp.status_code == 200
    assert "Bạn chưa tham gia khóa học nào" in resp.content.decode("utf-8")

@pytest.mark.django_db
def test_course_progress_view_requires_login(client):
    url = reverse("user_progress:progress")
    resp = client.get(url)
    assert resp.status_code in (302, 303)
    assert reverse("accounts:login") in resp.headers["Location"]
