# courses/urls.py
from django.urls import path
from . import views

app_name = "courses"

urlpatterns = [
    # ===== Course list / my courses =====
    path("", views.CourseListView.as_view(), name="list"),
    path("mine/", views.MyCoursesView.as_view(), name="my"),
    
    # ===== Lessons CRUD (authoring) by course_id =====
    path("<int:course_id>/lessons/",      views.LessonListView.as_view(),   name="lesson_list"),
    path("<int:course_id>/lessons/new/",  views.LessonCreateView.as_view(), name="lesson_create"),
    path("lessons/<int:pk>/edit/",        views.LessonUpdateView.as_view(), name="lesson_update"),
    path("lessons/<int:pk>/delete/",      views.LessonDeleteView.as_view(), name="lesson_delete"),

    # ===== Course progress =====
    path("<int:course_id>/progress/",     views.CourseProgressView.as_view(), name="course_progress"),

    # ===== Learn view (playlist) =====
    # by-id
    path("by-id/<int:course_id>/learn/<int:lesson_id>/", views.LessonLearnView.as_view(), name="lesson_by_id"),
    path("lesson/<int:lesson_id>/complete/", views.lesson_complete, name="lesson_complete"),
    # by-slug
    path("<slug:slug>/learn/<int:lesson_id>/",           views.LessonLearnView.as_view(), name="lesson"),

    # ===== Single lesson detail (optional page) =====
    path("<slug:slug>/lesson/<int:pk>/",  views.LessonDetailView.as_view(), name="lesson_detail"),

    # ===== QUIZ routes =====
    # by-id
    path("by-id/<int:course_id>/quiz/<int:lesson_id>/start/",    views.QuizStartView.as_view(),  name="quiz_start_by_id"),
    path("by-id/<int:course_id>/quiz/take/<int:submission_id>/", views.QuizTakeView.as_view(),   name="quiz_take_by_id"),
    path("by-id/<int:course_id>/quiz/result/<int:submission_id>/", views.QuizResultView.as_view(), name="quiz_result_by_id"),
    # by-slug
    path("<slug:slug>/quiz/<int:lesson_id>/start/",    views.QuizStartView.as_view(),  name="quiz_start"),
    path("<slug:slug>/quiz/take/<int:submission_id>/", views.QuizTakeView.as_view(),   name="quiz_take"),
    path("<slug:slug>/quiz/result/<int:submission_id>/", views.QuizResultView.as_view(), name="quiz_result"),

    # ===== Start & Enroll (course-level actions) =====
    # by-id
    path("by-id/<int:pk>/start/",   views.start_course_id,   name="start_by_id"),
    path("by-id/<int:pk>/enroll/",  views.enroll_request_id,    name="enroll_by_id"),
    # by-slug
    path("<slug:slug>/start/",      views.start_course_slug, name="start"),
    path("<slug:slug>/enroll/",     views.enroll_request_slug, name="enroll"),

    # ===== Course detail =====
    path("by-id/<int:pk>/", views.CourseDetailView.as_view(), name="detail_by_id"),
    path("<slug:slug>/",    views.CourseDetailView.as_view(), name="detail"),

    # ===== Enrollment admin action (optional) =====
    path("enrollment/<int:enrollment_id>/approve/", views.approve_enrollment, name="approve_enrollment"),
    
    # Đánh giá khóa học
    path('<int:course_id>/reviews/', views.CourseReviewListView.as_view(), name='review_list'),
    path('<int:course_id>/review/submit/', views.CourseReviewSubmitView.as_view(), name='review_submit'),
]
