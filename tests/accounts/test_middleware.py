import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

@pytest.mark.django_db
def test_blocked_user_redirected_to_login(client):
    User = get_user_model()
    u = User.objects.create_user(email="blocked@example.com", username="blocked@example.com", password="12345678")
    u.is_blocked = True
    u.save()

    client.force_login(u)
    resp = client.get(reverse("accounts:profile"))
    assert resp.status_code in (302, 303)
    assert reverse("accounts:login") in resp.headers["Location"]
