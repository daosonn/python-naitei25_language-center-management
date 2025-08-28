
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

@csrf_protect
def register_view(request):
	if request.method == "POST":
		full_name = request.POST.get("full_name")
		email = request.POST.get("email")
		password1 = request.POST.get("password1")
		password2 = request.POST.get("password2")
		agree = request.POST.get("agree")
		if not all([full_name, email, password1, password2, agree]):
			messages.error(request, "Vui lòng điền đầy đủ thông tin và đồng ý điều khoản.")
		elif password1 != password2:
			messages.error(request, "Mật khẩu không khớp.")
		elif User.objects.filter(email=email).exists():
			messages.error(request, "Email đã tồn tại.")
		else:
			user = User.objects.create_user(username=email, email=email, password=password1, first_name=full_name)
			messages.success(request, "Đăng ký thành công! Bạn có thể đăng nhập.")
			return redirect("/")
	return redirect("/")

@csrf_protect
def login_view(request: HttpRequest):
	if request.method == "POST":
		email = request.POST.get("email")
		password = request.POST.get("password")
		next_url = request.POST.get("next") or "/"
		user = authenticate(request, username=email, password=password)
		if user is not None:
			login(request, user)
			return redirect(next_url)
		else:
			return render(request, "accounts/login_modal.html", {"login_error": "Email hoặc mật khẩu không đúng.", "request": request})
	return redirect("/")

from .models import User, UserProfile

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

from .models import User, UserProfile

@login_required
def profile_view(request):
	user = request.user
	try:
		profile = user.profile
	except Exception:
		profile = None


	if request.method == 'POST':
		# Nếu chỉ upload avatar
		if 'avatar' in request.FILES:
			avatar = request.FILES['avatar']
			if profile:
				profile.avatar = avatar
				profile.save()
				messages.success(request, 'Cập nhật ảnh đại diện thành công!')
			else:
				messages.error(request, 'Không tìm thấy hồ sơ người dùng!')
			return redirect('accounts:profile')

		display_name = request.POST.get('display_name', '').strip()
		birthday = request.POST.get('birthday')
		phone = request.POST.get('phone', '').strip()
		japanese_level = request.POST.get('japanese_level', '').strip()
		address = request.POST.get('address', '').strip()
		country = request.POST.get('country', '').strip()

		# Validate và cập nhật
		if profile:
			profile.display_name = display_name
			profile.phone = phone
			profile.japanese_level = japanese_level
			profile.address = address
			profile.country = country
			if birthday:
				profile.birthday = birthday
			if 'avatar' in request.FILES:
				profile.avatar = request.FILES['avatar']
			profile.save()
			messages.success(request, 'Cập nhật thông tin thành công!')
		else:
			messages.error(request, 'Không tìm thấy hồ sơ người dùng!')
		return redirect('accounts:profile')

	context = {
		'user': user,
		'profile': profile,
		'completed_courses': [],  # TODO: tích hợp sau
	}
	return render(request, 'accounts/profile/profile.html', context)

@login_required
def change_password_view(request):
	if request.method == 'POST':
		form = PasswordChangeForm(request.user, request.POST)
		if form.is_valid():
			user = form.save()
			update_session_auth_hash(request, user)  # Giữ đăng nhập
			messages.success(request, 'Đổi mật khẩu thành công!')
			return redirect('accounts:profile')
	else:
		form = PasswordChangeForm(request.user)
	return render(request, 'accounts/profile/change_password.html', {'form': form})

# ...existing code...

def logout_view(request):
	logout(request)
	return redirect('/')