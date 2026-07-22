from django.urls import path

from . import views

app_name = "subscriptions"

urlpatterns = [
    path("", views.subscription_list, name="subscription_list"),
    path("add/", views.subscription_create, name="subscription_create"),
    path("<int:pk>/", views.subscription_detail, name="subscription_detail"),
    path("<int:pk>/edit/", views.subscription_edit, name="subscription_edit"),
]

