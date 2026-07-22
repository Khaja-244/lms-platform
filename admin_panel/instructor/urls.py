from django.urls import path

from . import views

app_name = "instructor"

urlpatterns = [
    path("", views.login_view, name="login"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
]
