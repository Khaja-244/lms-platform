from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("", views.payment_list, name="payment_list"),
    path("<int:pk>/", views.payment_detail, name="payment_detail"),
    path("<int:pk>/invoice/", views.payment_invoice, name="payment_invoice"),
]
