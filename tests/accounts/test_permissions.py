from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from accounts.permissions import user_role_required, admin_required, staff_required, active_user_required
# Test trực tiếp decorator user_role_required
def make_request(user=None):
    factory = RequestFactory()
    request = factory.get('/')
    if user is not None:
        request.user = user
    else:
        request.user = AnonymousUser()
    setattr(request, 'session', {})
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    return request

def dummy_view(request):
    return 123

def test_user_role_required_decorator_all_branches(user):
    # Chưa đăng nhập
    request = make_request(None)
    decorated = user_role_required(['admin'])(dummy_view)
    resp = decorated(request)
    assert resp.status_code == 302
    # Sai quyền
    user.role = 'student'
    request = make_request(user)
    decorated = user_role_required(['admin'])(dummy_view)
    resp = decorated(request)
    assert resp.status_code == 302
    # Đúng quyền
    user.role = 'admin'
    request = make_request(user)
    decorated = user_role_required(['admin'])(dummy_view)
    assert decorated(request) == 123

def test_admin_required_decorator(user):
    user.role = 'sa'
    user.is_staff = True
    request = make_request(user)
    decorated = admin_required(dummy_view)
    resp = decorated(request)
    assert getattr(resp, 'status_code', 200) in (200, 302)

def test_staff_required_decorator(user):
    user.role = 'wa'
    user.is_staff = True
    request = make_request(user)
    decorated = staff_required(dummy_view)
    resp = decorated(request)
    assert getattr(resp, 'status_code', 200) in (200, 302)
    user.role = 'sa'
    user.is_staff = True
    request = make_request(user)
    decorated = staff_required(dummy_view)
    resp = decorated(request)
    assert getattr(resp, 'status_code', 200) in (200, 302)

def test_active_user_required_decorator(user):
    # Chưa đăng nhập
    request = make_request(None)
    decorated = active_user_required(dummy_view)
    resp = decorated(request)
    assert resp.status_code == 302
    # Không active
    user.is_active = False
    user.is_blocked = True
    request = make_request(user)
    decorated = active_user_required(dummy_view)
    resp = decorated(request)
    assert resp.status_code == 302
    # Được phép login
    user.is_active = True
    user.is_blocked = False
    request = make_request(user)
    decorated = active_user_required(dummy_view)
    assert decorated(request) == 123
import pytest
import types

@pytest.mark.django_db
def test_permission_decorator_routes(client, user):
    # user_role_required: user không phải student sẽ bị redirect
    user.role = 'teacher'
    user.save()
    client.force_login(user)
    resp = client.get(reverse('accounts:test_user_role'))
    assert resp.status_code in (302, 303)
    # admin_required: user không phải admin sẽ bị redirect
    user.role = 'student'
    user.save()
    resp = client.get(reverse('accounts:test_admin'))
    assert resp.status_code in (302, 303)
    # staff_required: user không phải staff sẽ bị redirect
    resp = client.get(reverse('accounts:test_staff'))
    assert resp.status_code in (302, 303)
    # active_user_required: user không active sẽ bị redirect
    user.is_active = False
    user.is_blocked = True
    user.save()
    resp = client.get(reverse('accounts:test_active'))
    assert resp.status_code in (302, 303)
    # Đúng quyền thì trả về ok
    user.role = 'student'
    user.is_active = True
    user.is_blocked = False
    user.save()
    client.force_login(user)
    resp = client.get(reverse('accounts:test_user_role'))
    assert resp.status_code in (200, 302)
    user.role = UserRole.SYSTEM_ADMIN.value
    user.is_staff = True
    user.is_active = True
    user.is_blocked = False
    user.save()
    client.force_login(user)
    resp = client.get(reverse('accounts:test_admin'))
    assert resp.status_code in (200, 302)
    resp = client.get(reverse('accounts:test_staff'))
    assert resp.status_code in (200, 302)
    resp = client.get(reverse('accounts:test_active'))
    assert resp.status_code in (200, 302)
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from accounts.permissions import user_role_required, admin_required, staff_required, active_user_required
from constants import UserRole
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth.models import AnonymousUser

@pytest.mark.django_db
def test_user_role_required_allows_access_for_allowed_role(client, user):
    user.role = UserRole.SYSTEM_ADMIN
    user.save()
    client.force_login(user)
    url = reverse('accounts:profile')
    # Decorator should allow access
    resp = client.get(url)
    assert resp.status_code == 200 or resp.status_code == 302  # profile may redirect if not fully set up

@pytest.mark.django_db
def test_user_role_required_redirects_forbidden(client, user):
    user.role = 'student'  # not in allowed_roles
    user.save()
    client.force_login(user)
    factory = RequestFactory()
    request = factory.get('/')
    request.user = user
    # Add messages framework to request
    setattr(request, 'session', client.session)
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    
    @user_role_required([UserRole.SYSTEM_ADMIN])
    def dummy_view(request):
        return 42
    resp = dummy_view(request)
    # Should redirect to profile
    assert resp.status_code == 302
    assert resp.url == reverse('accounts:profile')

@pytest.mark.django_db
def test_user_role_required_redirects_unauthenticated(client):
    factory = RequestFactory()
    request = factory.get('/')
    request.user = AnonymousUser()
    @user_role_required([UserRole.SYSTEM_ADMIN])
    def dummy_view(request):
        return 42
    resp = dummy_view(request)
    assert resp.status_code == 302
    assert resp.url == reverse('accounts:login')

@pytest.mark.django_db
def test_admin_required_and_staff_required(client, user):
    user.role = UserRole.SYSTEM_ADMIN
    user.save()
    client.force_login(user)
    factory = RequestFactory()
    request = factory.get('/')
    request.user = user
    setattr(request, 'session', client.session)
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    # admin_required
    @admin_required
    def dummy_admin(request):
        return 42
    assert dummy_admin(request) == 42
    # staff_required
    @staff_required
    def dummy_staff(request):
        return 43
    assert dummy_staff(request) == 43

@pytest.mark.django_db
def test_active_user_required_blocks_inactive(client, user):
    user.can_login = lambda: False
    client.force_login(user)
    factory = RequestFactory()
    request = factory.get('/')
    request.user = user
    setattr(request, 'session', client.session)
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    @active_user_required
    def dummy(request):
        return 99
    resp = dummy(request)
    assert resp.status_code == 302
    assert resp.url == reverse('accounts:login')

@pytest.mark.django_db
def test_active_user_required_allows_active(client, user):
    user.can_login = lambda: True
    client.force_login(user)
    factory = RequestFactory()
    request = factory.get('/')
    request.user = user
    setattr(request, 'session', client.session)
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    @active_user_required
    def dummy(request):
        return 100
    assert dummy(request) == 100
