from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("django-admin/", admin.site.urls),

    # Dashboard
    path("", include("dashboard.urls")),

    # Student Portal
    path("student/", include("student.urls")),
    path("instructor/", include("instructor.urls")),

    # User Management
    path("accounts/", include("accounts.urls")),

    # Course Management
    path("courses/", include("courses.urls")),

    # Subscription Platform
    path("plans/", include("plans.urls")),
    path("subscriptions/", include("subscriptions.urls")),
    path("payments/", include("payments.urls")),
    path("analytics/", include("analytics.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
