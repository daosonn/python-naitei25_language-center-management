import pytest
from accounts.pipeline import prevent_duplicate_social_email
from django.contrib.auth import get_user_model
from social_core.exceptions import AuthForbidden
from unittest import mock

User = get_user_model()

@pytest.mark.django_db
def test_prevent_duplicate_social_email_blocks_duplicate_email(user):
    backend = mock.Mock()
    backend.name = 'google-oauth2'
    backend.strategy.storage.user.get_social_auth.return_value = None
    details = {'email': user.email}
    with pytest.raises(AuthForbidden):
        prevent_duplicate_social_email(backend, details, uid='123')

@pytest.mark.django_db
def test_prevent_duplicate_social_email_allows_new_email():
    backend = mock.Mock()
    backend.name = 'google-oauth2'
    backend.strategy.storage.user.get_social_auth.return_value = None
    details = {'email': 'unique@example.com'}
    # Không có user, không raise
    prevent_duplicate_social_email(backend, details, uid='123')

@pytest.mark.django_db
def test_prevent_duplicate_social_email_allows_linked_social(user):
    backend = mock.Mock()
    backend.name = 'google-oauth2'
    backend.strategy.storage.user.get_social_auth.return_value = True
    details = {'email': user.email}
    # Đã có social, không raise
    prevent_duplicate_social_email(backend, details, uid='123')

@pytest.mark.django_db
def test_prevent_duplicate_social_email_no_email():
    backend = mock.Mock()
    details = {}
    # Không có email, không raise
    prevent_duplicate_social_email(backend, details, uid='123')
