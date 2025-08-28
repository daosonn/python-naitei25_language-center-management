# Jazzmin custom menu order for Django admin
JAZZMIN_SETTINGS = {
    "order_with_respect_to": [
        "accounts",
        "courses",
        "quizzes",
        "user_progress",
        "custom_admin",
        "notifications",
        "nested_admin",
        "django_recaptcha",
        "django.contrib.admin",
        "django.contrib.staticfiles",
        "social_django",
        "auth",  # Django auth (Groups, Users)
    ],
}
