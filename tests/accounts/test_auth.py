import pytest
from django.urls import reverse

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

@pytest.mark.django_db
def test_login_success_redirects(client, user, user_password):
    url = reverse("accounts:login")
    resp = client.post(url, {"email": "son@example.com", "password": user_password, "next": "/"})
    assert resp.status_code in (302, 303)
    assert resp.headers["Location"].endswith("/")

@pytest.mark.django_db
def test_profile_requires_login_redirect(client):
    url = reverse("accounts:profile")
    resp = client.get(url)
    # Middleware buộc login, nên 302 về /accounts/login/?next=...
    assert resp.status_code in (302, 303)
    assert reverse("accounts:login") in resp.headers["Location"]


# --- Register view tests ---
@pytest.mark.django_db
def test_register_missing_fields(client):
    url = reverse("accounts:register")
    resp = client.post(url, {})
    assert resp.status_code in (302, 303)
    # Kiểm tra có thông báo lỗi

@pytest.mark.django_db
def test_register_password_mismatch(client):
    url = reverse("accounts:register")
    resp = client.post(url, {
        "full_name": "Test User",
        "email": "test@ex.com",
        "password1": "abc",
        "password2": "def",
        "agree": "on",
    })
    assert resp.status_code in (302, 303)

@pytest.mark.django_db
def test_register_email_exists(client, user):
    url = reverse("accounts:register")
    resp = client.post(url, {
        "full_name": "Test User",
        "email": user.email,
        "password1": "abc",
        "password2": "abc",
        "agree": "on",
    })
    assert resp.status_code in (302, 303)

@pytest.mark.django_db
def test_register_success(client):
    url = reverse("accounts:register")
    email = "newuser@ex.com"
    resp = client.post(url, {
        "full_name": "Test User",
        "email": email,
        "password1": "StrongPass123!",
        "password2": "StrongPass123!",
        "agree": "on",
    })
    assert resp.status_code in (302, 303)
    User = get_user_model()
    assert User.objects.filter(email=email).exists()

# --- Login view tests ---
@pytest.mark.django_db
def test_login_wrong_password(client, user):
    url = reverse("accounts:login")
    resp = client.post(url, {"email": user.email, "password": "wrong"})
    assert resp.status_code == 200
    assert "mật khẩu không đúng" in resp.content.decode().lower()

@pytest.mark.django_db
def test_login_get_redirect(client):
    url = reverse("accounts:login")
    resp = client.get(url)
    assert resp.status_code in (302, 303)

# --- Profile view tests ---
@pytest.mark.django_db
def test_profile_get(auth_client):
    url = reverse("accounts:profile")
    resp = auth_client.get(url)
    assert resp.status_code == 200
    assert "profile" in resp.content.decode().lower()

@pytest.mark.django_db
def test_profile_update_info(auth_client):
    url = reverse("accounts:profile")
    resp = auth_client.post(url, {
        "display_name": "New Name",
        "phone": "123456",
        "japanese_level": "N5",
        "address": "Hanoi",
        "country": "VN",
    })
    assert resp.status_code in (302, 303)

@pytest.mark.django_db
def test_profile_update_avatar(auth_client, tmp_path):
    url = reverse("accounts:profile")
    img = SimpleUploadedFile("avatar.png", b"filecontent", content_type="image/png")
    resp = auth_client.post(url, {"avatar": img})
    assert resp.status_code in (302, 303)

# --- Change password view tests ---
@pytest.mark.django_db
def test_change_password_get(auth_client):
    url = reverse("accounts:change_password")
    resp = auth_client.get(url)
    assert resp.status_code == 200

@pytest.mark.django_db
def test_change_password_post_invalid(auth_client):
    url = reverse("accounts:change_password")
    resp = auth_client.post(url, {"old_password": "wrong", "new_password1": "a", "new_password2": "b"})
    assert resp.status_code == 200

# --- Logout view test ---
@pytest.mark.django_db
def test_logout(client, user):
    client.force_login(user)
    url = reverse("accounts:logout")
    resp = client.get(url)
    assert resp.status_code in (302, 303)
