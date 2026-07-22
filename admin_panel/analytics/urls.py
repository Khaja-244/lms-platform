from django.urls import path

from . import views

app_name = "analytics"

urlpatterns = [
    path("", views.analytics_dashboard, name="dashboard"),
    path("dashboard/", views.course_dashboard_json, name="course_dashboard_json"),
    path("notifications/", views.notification_list, name="notification_list"),
    path("notifications/create/", views.notification_create, name="notification_create"),
    path("notifications/mark-all-read/", views.notification_mark_all_read, name="notification_mark_all_read"),
    path("notifications/<int:pk>/read/", views.notification_mark_read, name="notification_mark_read"),
]
