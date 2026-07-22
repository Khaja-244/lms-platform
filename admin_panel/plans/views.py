from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PlanForm
from .models import Plan


@login_required
def plan_list(request):
    plans = Plan.objects.all()
    return render(request, "plans/plan_list.html", {"plans": plans})


@login_required
def plan_create(request):
    if request.method == "POST":
        form = PlanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Plan created successfully.")
            return redirect("plans:plan_list")
    else:
        form = PlanForm()

    return render(request, "plans/plan_form.html", {"form": form, "title": "Add Plan"})


@login_required
def plan_edit(request, pk):
    plan = get_object_or_404(Plan, pk=pk)

    if request.method == "POST":
        form = PlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, "Plan updated successfully.")
            return redirect("plans:plan_list")
    else:
        form = PlanForm(instance=plan)

    return render(request, "plans/plan_form.html", {"form": form, "title": "Edit Plan"})


@login_required
def plan_delete(request, pk):
    plan = get_object_or_404(Plan, pk=pk)

    if request.method == "POST":
        plan.delete()
        messages.success(request, "Plan deleted successfully.")
        return redirect("plans:plan_list")

    return render(request, "plans/plan_confirm_delete.html", {"plan": plan})


