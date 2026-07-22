"""
accounts/views.py

Two responsibilities, matching the task spec:
1. Admin Authentication (login/logout)
2. User & Instructor Management (CRUD)
"""

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AdminLoginForm, UserForm
from .models import User, UserRole


class AdminLoginView(LoginView):
    """Bootstrap Login Page"""

    template_name = "accounts/login.html"
    authentication_form = AdminLoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        remember_me = self.request.POST.get("remember_me")

        if remember_me:
            self.request.session.set_expiry(60 * 60 * 24 * 14)  # 14 days
        else:
            self.request.session.set_expiry(0)

        return super().form_valid(form)


@login_required
def admin_logout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("accounts:login")


@login_required
def user_list(request):
    """
    User & Instructor List
    Supports:
    - Search
    - Role Filter
    - Django Pagination
    """

    role_filter = request.GET.get("role", "")
    search = request.GET.get("search", "").strip()

    users = User.objects.exclude(
        role=UserRole.ADMIN
    )

    # Role Filter
    if role_filter in (
        UserRole.STUDENT,
        UserRole.INSTRUCTOR,
    ):
        users = users.filter(
            role=role_filter
        )

    # Search
    if search:
        from django.db.models import Q

        users = users.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search)
        )

    users = users.order_by("-date_joined")

    paginator = Paginator(users, 8)

    page_number = request.GET.get("page", 1)

    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "accounts/user_list.html",
        {
            "users": page_obj,
            "page_obj": page_obj,
            "role_filter": role_filter,
            "search": search,
        },
    )


@login_required
def user_create(request):

    if request.method == "POST":

        form = UserForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(request, "User created successfully.")

            return redirect("accounts:user_list")

    else:
        form = UserForm()

    return render(
        request,
        "accounts/user_form.html",
        {
            "form": form,
            "title": "Add User",
        },
    )


@login_required
def user_edit(request, pk):

    user = get_object_or_404(User, pk=pk)

    if request.method == "POST":

        form = UserForm(request.POST, instance=user)

        if form.is_valid():
            form.save()

            messages.success(request, "User updated successfully.")

            return redirect("accounts:user_list")

    else:
        form = UserForm(instance=user)

    return render(
        request,
        "accounts/user_form.html",
        {
            "form": form,
            "title": "Edit User",
        },
    )


@login_required
def user_delete(request, pk):

    user = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        user.delete()

        messages.success(request, "User deleted successfully.")

        return redirect("accounts:user_list")

    return render(
        request,
        "accounts/user_confirm_delete.html",
        {
            "user_obj": user,
        },
    )