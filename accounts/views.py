from django.contrib import messages
from django.contrib.auth import (
    authenticate, login, logout, update_session_auth_hash, get_user_model
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_date

from .models import UserProfile
from constants import JAPANESE_LEVEL_CHOICES, COUNTRY_CHOICES


@csrf_protect
@require_POST
def register_view(request):
    """
    Đăng ký tài khoản bằng email (email = username).
    """
    full_name = (request.POST.get("full_name") or "").strip()
    email = (request.POST.get("email") or "").strip().lower()
    password1 = request.POST.get("password1")
    password2 = request.POST.get("password2")
    agree = request.POST.get("agree")

    User = get_user_model()

    if not all([full_name, email, password1, password2, agree]):
        messages.error(request, _("Vui lòng điền đầy đủ thông tin và đồng ý điều khoản."))
        return redirect("/")

    if password1 != password2:
        messages.error(request, _("Mật khẩu không khớp."))
        return redirect("/")

    if User.objects.filter(email__iexact=email).exists():
        messages.error(request, _("Email đã tồn tại."))
        return redirect("/")

    # Tạo user (username = email để đồng nhất với authenticate)
    user = User.objects.create_user(username=email, email=email, password=password1)
    if hasattr(user, "first_name"):
        user.first_name = full_name
        user.save(update_fields=["first_name"])

    # Đảm bảo có hồ sơ
    UserProfile.objects.get_or_create(user=user)

    messages.success(request, _("Đăng ký thành công! Bạn có thể đăng nhập."))
    return redirect("/")


@csrf_protect
def login_view(request):
    """
    Đăng nhập bằng email (dùng email làm username).
    """
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password")
        next_url = request.POST.get("next") or "/"

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect(next_url)

        # Sai thông tin -> render modal để hiển thị lỗi
        return render(
            request,
            "accounts/login_modal.html",
            {"login_error": _("Email hoặc mật khẩu không đúng."), "request": request},
        )

    return redirect("/")


@login_required
def profile_view(request):
    """
    Trang hồ sơ: cập nhật avatar + thông tin cơ bản.
    """
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == "POST":
        # Upload avatar nhanh
        if "avatar" in request.FILES:
            profile.avatar = request.FILES["avatar"]
            profile.save(update_fields=["avatar"])
            messages.success(request, _("Cập nhật ảnh đại diện thành công!"))
            return redirect("accounts:profile")

        # Cập nhật thông tin khác
        display_name = (request.POST.get("display_name") or "").strip()
        birthday_raw = (request.POST.get("birthday") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        japanese_level = (request.POST.get("japanese_level") or "").strip()
        address = (request.POST.get("address") or "").strip()
        country = (request.POST.get("country") or "").strip()

        profile.display_name = display_name or profile.display_name
        profile.phone = phone
        profile.japanese_level = japanese_level
        profile.address = address
        profile.country = country

        if birthday_raw:
            dt = parse_date(birthday_raw)
            if dt:
                profile.birthday = dt

        profile.save()
        messages.success(request, _("Cập nhật thông tin thành công!"))
        return redirect("accounts:profile")

    context = {
        "user": user,
        "profile": profile,
        "JAPANESE_LEVEL_CHOICES": JAPANESE_LEVEL_CHOICES,
        "COUNTRY_CHOICES": COUNTRY_CHOICES,
        "completed_courses": [],  # TODO: tích hợp sau
    }
    return render(request, "accounts/profile/profile.html", context)


@login_required
def change_password_view(request):
    """
    Đổi mật khẩu, giữ đăng nhập sau khi đổi.
    """
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # giữ phiên đăng nhập
            messages.success(request, _("Đổi mật khẩu thành công!"))
            return redirect("accounts:profile")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, "accounts/profile/change_password.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("/")
