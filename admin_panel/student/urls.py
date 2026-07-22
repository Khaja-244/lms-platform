from django.urls import path
from . import views

app_name = "student"

urlpatterns = [
    path("", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("courses/", views.courses_view, name="courses"),
    path("course/<int:course_id>/", views.course_detail_view, name="course_detail"),
    path("my-courses/", views.my_courses_view, name="my_courses"),
    path("lesson/<int:lesson_id>/", views.lesson_player_view, name="lesson_player"),
    path("plans/", views.plans_view, name="plans"),
    path("subscription/", views.subscription_view, name="subscription"),
    path("payments/", views.payments_view, name="payments"),
    path("notifications/", views.notifications_view, name="notifications"),
    path("assignments/", views.assignments_view, name="assignments"),
    path("attendance/", views.attendance_view, name="attendance"),
    path("chat/", views.chat_view, name="chat"),
    path("profile/", views.profile_view, name="profile"),
]
