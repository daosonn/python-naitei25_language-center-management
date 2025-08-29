import pytest
from courses.mixins import CourseAccessRequiredMixin, _guard_course_access
from unittest import mock
from django.http import HttpResponse, HttpResponseForbidden

from django.http import HttpResponseForbidden
class DummySuper:
    def dispatch(self, request, *args, **kwargs):
        if getattr(request, 'forbidden', False):
            return HttpResponseForbidden('forbidden')
        return HttpResponse('ok')

@pytest.mark.django_db
def test_course_access_required_mixin_slug_found(monkeypatch):
    # Mock Course, user, request
    mixin = type('TestView', (CourseAccessRequiredMixin, DummySuper), {})()
    request = mock.Mock()
    request.user.is_authenticated = True
    request.user.is_superuser = True
    # slug có, Course có slug field
    monkeypatch.setattr('courses.mixins.Course._meta.get_field', lambda name: True)
    monkeypatch.setattr('courses.mixins.get_object_or_404', lambda model, slug=None: mock.Mock())
    monkeypatch.setattr('courses.mixins.user_can_access_course', lambda user, course: True)
    request.forbidden = False
    resp = mixin.dispatch(request, slug='abc')
    assert resp.status_code == 200

@pytest.mark.django_db
def test_course_access_required_mixin_course_id(monkeypatch):
    mixin = type('TestView', (CourseAccessRequiredMixin, DummySuper), {})()
    request = mock.Mock()
    request.user.is_authenticated = True
    request.user.is_superuser = True
    monkeypatch.setattr('courses.mixins.Course._meta.get_field', lambda name: True)
    monkeypatch.setattr('courses.mixins.get_object_or_404', lambda model, pk=None: mock.Mock())
    monkeypatch.setattr('courses.mixins.user_can_access_course', lambda user, course: True)
    request.forbidden = False
    resp = mixin.dispatch(request, course_id=1)
    assert resp.status_code == 200

@pytest.mark.django_db
def test_course_access_required_mixin_lesson_id(monkeypatch):
    mixin = type('TestView', (CourseAccessRequiredMixin, DummySuper), {})()
    request = mock.Mock()
    request.user.is_authenticated = True
    request.user.is_superuser = True
    lesson = mock.Mock()
    lesson.course = mock.Mock()
    monkeypatch.setattr('courses.mixins.get_object_or_404', lambda model, pk=None: lesson)
    monkeypatch.setattr('courses.mixins.user_can_access_course', lambda user, course: True)
    request.forbidden = False
    resp = mixin.dispatch(request, lesson_id=1)
    assert resp.status_code == 200

@pytest.mark.django_db
def test_course_access_required_mixin_no_course():
    mixin = type('TestView', (CourseAccessRequiredMixin, DummySuper), {})()
    request = mock.Mock()
    request.user.is_authenticated = True
    request.user.is_superuser = True
    # Không có slug, id, lesson_id
    request.forbidden = True
    resp = mixin.dispatch(request)
    assert resp.status_code == 403

@pytest.mark.django_db
def test_course_access_required_mixin_no_access(monkeypatch):
    mixin = type('TestView', (CourseAccessRequiredMixin, DummySuper), {})()
    request = mock.Mock()
    request.user.is_authenticated = True
    request.user.is_superuser = False
    # slug có, Course có slug field
    course = mock.Mock()
    monkeypatch.setattr('courses.mixins.Course._meta.get_field', lambda name: True)
    monkeypatch.setattr('courses.mixins.get_object_or_404', lambda model, slug=None: course)
    monkeypatch.setattr('courses.mixins.user_can_access_course', lambda user, course: False)
    request.forbidden = True
    resp = mixin.dispatch(request, slug='abc')
    assert resp.status_code == 403

@pytest.mark.django_db
def test_guard_course_access(monkeypatch):
    request = mock.Mock()
    request.user = mock.Mock()
    course = mock.Mock()
    monkeypatch.setattr('courses.mixins.user_can_access_course', lambda user, course: False)
    result = _guard_course_access(request, course)
    assert result is False
    monkeypatch.setattr('courses.mixins.user_can_access_course', lambda user, course: True)
    result = _guard_course_access(request, course)
    assert result is True
