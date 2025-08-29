import pytest
from accounts.forms import ChangePasswordForm, ProfileUpdateForm
from accounts.models import User, UserProfile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from datetime import date

@pytest.mark.django_db
def test_change_password_form_valid(user):
    user.set_password('oldpass123')
    user.save()
    form = ChangePasswordForm(user, data={
        'current_password': 'oldpass123',
        'new_password': 'newpass123',
        'confirm_password': 'newpass123',
    })
    assert form.is_valid(), form.errors

@pytest.mark.django_db
def test_change_password_form_wrong_current(user):
    user.set_password('oldpass123')
    user.save()
    form = ChangePasswordForm(user, data={
        'current_password': 'wrongpass',
        'new_password': 'newpass123',
        'confirm_password': 'newpass123',
    })
    assert not form.is_valid()
    assert 'current_password' in form.errors

@pytest.mark.django_db
def test_change_password_form_mismatch(user):
    user.set_password('oldpass123')
    user.save()
    form = ChangePasswordForm(user, data={
        'current_password': 'oldpass123',
        'new_password': 'newpass123',
        'confirm_password': 'otherpass',
    })
    assert not form.is_valid()
    assert '__all__' in form.errors

@pytest.mark.django_db
def test_profile_update_form_valid(user):
    profile = user.profile
    data = {
        'full_name': 'Test User',
        'phone_number': '0123456789',
        'japanese_level': 'N3',
        'address': 'Hanoi',
        'country': 'VN',
        'display_name': 'Tester',
        'gender': 'm',
        'birthday': date(2000, 1, 1),
        'is_locked': False,
    }
    form = ProfileUpdateForm(data, instance=profile)
    assert form.is_valid(), form.errors
    updated = form.save()
    assert updated.full_name == 'Test User'

@pytest.mark.django_db
def test_profile_update_form_avatar_size(user):
    profile = user.profile
    big_file = SimpleUploadedFile('big.jpg', b'a' * (6 * 1024 * 1024), content_type='image/jpeg')
    data = {
        'full_name': 'Test User',
        'phone_number': '0123456789',
        'japanese_level': 'N3',
        'address': 'Hanoi',
        'country': 'VN',
        'display_name': 'Tester',
        'gender': 'm',
        'birthday': date(2000, 1, 1),
        'is_locked': False,
    }
    form = ProfileUpdateForm(data, {'avatar': big_file}, instance=profile)
    form.is_valid()
    assert 'avatar' in form.errors

@pytest.mark.django_db
def test_profile_update_form_avatar_type(user):
    profile = user.profile
    bad_file = SimpleUploadedFile('bad.txt', b'abc', content_type='text/plain')
    data = {
        'full_name': 'Test User',
        'phone_number': '0123456789',
        'japanese_level': 'N3',
        'address': 'Hanoi',
        'country': 'VN',
        'display_name': 'Tester',
        'gender': 'm',
        'birthday': date(2000, 1, 1),
        'is_locked': False,
    }
    form = ProfileUpdateForm(data, {'avatar': bad_file}, instance=profile)
    form.is_valid()
    assert 'avatar' in form.errors
