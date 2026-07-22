from django.urls import path

from . import views

app_name = "plans"

urlpatterns = [
    path("", views.plan_list, name="plan_list"),
    path("add/", views.plan_create, name="plan_create"),
    path("<int:pk>/edit/", views.plan_edit, name="plan_edit"),
    path("<int:pk>/delete/", views.plan_delete, name="plan_delete"),
]

