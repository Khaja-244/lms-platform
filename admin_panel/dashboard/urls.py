from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/top-courses/", views.top_courses_api, name="top_courses_api"),
]
