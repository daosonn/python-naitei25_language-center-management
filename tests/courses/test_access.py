import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_course_list_ok(client):
    resp = client.get(reverse("courses:list"))
    assert resp.status_code == 200  # render danh sách

@pytest.mark.django_db
def test_my_courses_requires_login(client):
    resp = client.get(reverse("courses:my"))
    assert resp.status_code in (302, 303)
    assert reverse("accounts:login") in resp.headers["Location"]
