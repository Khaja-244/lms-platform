from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SubscriptionForm
from .models import Subscription


@login_required
def subscription_list(request):
    subscriptions = Subscription.objects.select_related("user", "plan").all()
    return render(request, "subscriptions/subscription_list.html", {"subscriptions": subscriptions})


@login_required
def subscription_create(request):
    if request.method == "POST":
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Subscription created successfully.")
            return redirect("subscriptions:subscription_list")
    else:
        form = SubscriptionForm()

    return render(request, "subscriptions/subscription_form.html", {"form": form, "title": "Add Subscription"})


@login_required
def subscription_edit(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)

    if request.method == "POST":
        form = SubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            messages.success(request, "Subscription updated successfully.")
            return redirect("subscriptions:subscription_list")
    else:
        form = SubscriptionForm(instance=subscription)

    return render(request, "subscriptions/subscription_form.html", {"form": form, "title": "Edit Subscription"})


@login_required
def subscription_detail(request, pk):
    subscription = get_object_or_404(
        Subscription.objects.select_related("user", "plan"),
        pk=pk,
    )
    return render(request, "subscriptions/subscription_detail.html", {"subscription": subscription})


