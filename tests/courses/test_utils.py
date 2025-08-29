import pytest
from courses.utils import _extract_youtube_id, user_can_access_course
from types import SimpleNamespace
from unittest import mock

@pytest.mark.parametrize("url,expected", [
    ("https://youtu.be/abcdefghijk", "abcdefghijk"),
    ("https://www.youtube.com/watch?v=abcdefghijk", "abcdefghijk"),
    ("https://youtube.com/embed/abcdefghijk", "abcdefghijk"),
    ("https://youtube.com/shorts/abcdefghijk", "abcdefghijk"),
    ("https://www.youtube.com/watch?v=abcdefghijk&feature=share", "abcdefghijk"),
    ("", ""),
    ("https://example.com/", ""),
])
def test_extract_youtube_id(url, expected):
    assert _extract_youtube_id(url) == expected

@pytest.mark.django_db
def test_user_can_access_course_authenticated_superuser():
    user = SimpleNamespace(is_authenticated=True, is_superuser=True, is_staff=False)
    course = object()
    assert user_can_access_course(user, course)

@pytest.mark.django_db
def test_user_can_access_course_authenticated_staff():
    user = SimpleNamespace(is_authenticated=True, is_superuser=False, is_staff=True)
    course = object()
    assert user_can_access_course(user, course)

@pytest.mark.django_db
def test_user_can_access_course_not_authenticated():
    user = SimpleNamespace(is_authenticated=False, is_superuser=False, is_staff=False)
    course = object()
    assert not user_can_access_course(user, course)

import unittest.mock as umock

@pytest.mark.django_db
def test_user_can_access_course_enrolled():
    user = SimpleNamespace(is_authenticated=True, is_superuser=False, is_staff=False)
    course = object()
    with umock.patch('courses.utils.Enrollment.objects.filter') as mock_filter:
        mock_filter.return_value.exists.return_value = True
        assert user_can_access_course(user, course)
        mock_filter.return_value.exists.return_value = False
        assert not user_can_access_course(user, course)
