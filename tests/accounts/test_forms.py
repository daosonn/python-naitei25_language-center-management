import pytest
from accounts.forms import UserRegistrationForm, UserLoginForm
from accounts.models import User
from django.core.exceptions import ValidationError
from unittest import mock

@pytest.mark.django_db
def test_user_registration_form_valid():
    data = {
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': '12345678',
        'confirm_password': '12345678',
        'g-recaptcha-response': 'PASSED',
    }
    with mock.patch('django_recaptcha.fields.client.submit') as recaptcha_submit:
        recaptcha_submit.return_value.is_valid = True
        form = UserRegistrationForm(data)
        assert form.is_valid(), form.errors
        user = form.save()
        assert User.objects.filter(username='newuser').exists()
        assert user.check_password('12345678')

@pytest.mark.django_db
def test_user_registration_form_username_exists(user):
    data = {
        'username': user.username,
        'email': 'unique@example.com',
        'password': '12345678',
        'confirm_password': '12345678',
        'g-recaptcha-response': 'PASSED',
    }
    with mock.patch('django_recaptcha.fields.client.submit') as recaptcha_submit:
        recaptcha_submit.return_value.is_valid = True
        form = UserRegistrationForm(data)
        assert not form.is_valid()
        assert 'username' in form.errors

@pytest.mark.django_db
def test_user_registration_form_email_exists(user):
    data = {
        'username': 'uniqueuser',
        'email': user.email,
        'password': '12345678',
        'confirm_password': '12345678',
        'g-recaptcha-response': 'PASSED',
    }
    with mock.patch('django_recaptcha.fields.client.submit') as recaptcha_submit:
        recaptcha_submit.return_value.is_valid = True
        form = UserRegistrationForm(data)
        assert not form.is_valid()
        assert 'email' in form.errors

@pytest.mark.django_db
def test_user_registration_form_password_mismatch():
    data = {
        'username': 'userx',
        'email': 'userx@example.com',
        'password': '12345678',
        'confirm_password': '87654321',
        'g-recaptcha-response': 'PASSED',
    }
    with mock.patch('django_recaptcha.fields.client.submit') as recaptcha_submit:
        recaptcha_submit.return_value.is_valid = True
        form = UserRegistrationForm(data)
        assert not form.is_valid()
        assert '__all__' in form.errors

@pytest.mark.django_db
def test_user_login_form_valid(user, user_password):
    data = {
        'email': user.email,
        'password': user_password,
        'g-recaptcha-response': 'PASSED',
    }
    with mock.patch('django_recaptcha.fields.client.submit') as recaptcha_submit:
        recaptcha_submit.return_value.is_valid = True
        form = UserLoginForm(data)
        assert form.is_valid(), form.errors

@pytest.mark.django_db
def test_user_login_form_invalid():
    data = {
        'email': 'notfound@example.com',
        'password': 'wrongpass',
        'g-recaptcha-response': 'PASSED',
    }
    with mock.patch('django_recaptcha.fields.client.submit') as recaptcha_submit:
        recaptcha_submit.return_value.is_valid = True
        form = UserLoginForm(data)
        # Form chỉ kiểm tra định dạng, không check DB, nhưng có thể có lỗi '__all__' nếu custom clean
        assert not form.is_valid()
