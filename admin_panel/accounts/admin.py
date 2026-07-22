from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    Read/manage users from Django's built-in /django-admin/ screen.

    NOTE: We deliberately use a plain ModelAdmin here instead of
    django.contrib.auth.admin.UserAdmin. That base class assumes a
    `username` field (via UserCreationForm/UserChangeForm), which our
    custom User model doesn't have (we authenticate with `email`
    instead - see accounts/models.py). Subclassing it would raise a
    FieldError as soon as this page loads. Password changes for users
    are handled through the custom Bootstrap CRUD pages (accounts/views.py),
    which already hash passwords correctly via UserForm.save().
    """

    model = User
    list_display = ("id", "name", "email", "role", "is_active", "is_staff", "date_joined")
    list_filter = ("role", "is_active")
    search_fields = ("name", "email")
    ordering = ("-date_joined",)
    readonly_fields = ("password_display", "date_joined")

    fieldsets = (
        (None, {"fields": ("email", "password_display")}),
        ("Personal info", {"fields": ("name", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Important dates", {"fields": ("date_joined",)}),
    )

    @admin.display(description="Password")
    def password_display(self, obj):
        # Never show the raw hash in the UI. Password changes happen via
        # the Bootstrap "Edit User" page, which hashes correctly.
        return "•••••••• (change via Admin Panel > Users > Edit)"

    def has_add_permission(self, request):
        # Creating users here would need a password-set flow we haven't
        # built (BaseUserAdmin's is incompatible with our model, as above).
        # Use "Add User" in the Bootstrap Admin Panel instead, or
        # `python manage.py createsuperuser` for the first admin login.
        return False
