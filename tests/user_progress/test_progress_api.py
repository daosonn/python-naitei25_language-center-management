import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_mark_lesson_complete_requires_login(client, lesson):
    url = reverse("user_progress:mark_lesson_complete", args=[lesson.id])
    resp = client.post(url)
    assert resp.status_code in (302, 303)
    assert reverse("accounts:login") in resp.headers["Location"]

@pytest.mark.django_db
def test_mark_lesson_complete_ok(auth_client, lesson):
    url = reverse("user_progress:mark_lesson_complete", args=[lesson.id])
    resp = auth_client.post(url)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "created" in data
