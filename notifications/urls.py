# custom_admin/urls.py

from django.urls import path
from . import views

urlpatterns = [
	path('api/unread/', views.unread_notifications, name='notifications_unread'),
]
