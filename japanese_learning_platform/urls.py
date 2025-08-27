"""
Cấu hình URL chính của dự án.
Bao gồm các URL từ các ứng dụng con.
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from .settings import STATIC_ROOT, STATIC_URL, MEDIA_URL, MEDIA_ROOT
from django.urls import path, include
from courses.views import CourseListView, HomeView

urlpatterns = [
    path('admin/', include('nested_admin.urls')),
    path('admin/', admin.site.urls), # URL cho Django Admin mặc định
    path('custom-admin/', include('custom_admin.urls')), # URL cho hệ thống quản trị tùy chỉnh
    path('accounts/', include('accounts.urls')), # URL cho ứng dụng accounts
    path('courses/', include('courses.urls', namespace='courses')), # URL cho ứng dụng courses
    path('quizzes/', include('quizzes.urls', namespace='quizzes')),
    path('progress/', include('user_progress.urls', namespace='user_progress')), # URL cho ứng dụng user_progress
    path('notifications/', include('notifications.urls')), # URL cho ứng dụng notifications (nếu có views)
    path("", HomeView.as_view(), name='home'),
    path('oauth/', include('social_django.urls', namespace='social'))
]
                                                                                                                                                                                                                                                                                                                                                                                                                                                    
# Cấu hình phục vụ tệp media và static trong môi trường phát triển
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
