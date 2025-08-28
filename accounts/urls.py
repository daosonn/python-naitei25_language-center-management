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
]
