from django.urls import path
from . import views

app_name = 'user_progress'

urlpatterns = [
    path('', views.CourseProgressView.as_view(), name='progress'),
    path('lesson/<int:lesson_id>/complete/', 
         views.mark_lesson_complete, 
         name='mark_lesson_complete'),
]
