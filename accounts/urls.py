from django.urls import path
from django.http import HttpResponse
from . import views

app_name = 'accounts'

urlpatterns = [
    path("", lambda request: HttpResponse("Accounts Home")),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("profile/", views.profile_view, name="profile"),
    path("change-password/", views.change_password_view, name="change_password"),
    path("logout/", views.logout_view, name="logout"),
    # --- test permission decorators ---
    path("test/user-role/", __import__('accounts.testviews').testviews.user_role_view, name="test_user_role"),
    path("test/admin/", __import__('accounts.testviews').testviews.admin_view, name="test_admin"),
    path("test/staff/", __import__('accounts.testviews').testviews.staff_view, name="test_staff"),
    path("test/active/", __import__('accounts.testviews').testviews.active_user_view, name="test_active"),
]
