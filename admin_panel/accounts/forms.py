"""
accounts/forms.py

Plain Django forms used by the Bootstrap CRUD pages for managing
Users and Instructors from the Admin Panel.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import User, UserRole


class AdminLoginForm(AuthenticationForm):
    """Login form restricted to staff users (is_staff=True)."""

    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "you@example.com", "autofocus": True}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"}),
    )

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise forms.ValidationError(
                "This account does not have Admin Panel access.", code="not_staff"
            )

    def clean_username(self):
        email = self.cleaned_data["username"].strip().lower()
        if not email.endswith("@gmail.com"):
            raise forms.ValidationError("Enter a Gmail address ending with @gmail.com.")
        return email


class UserForm(forms.ModelForm):
    """Used to create/edit Users and Instructors (role picks which)."""

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=False,
        help_text="Leave blank to keep the current password when editing.",
    )

    class Meta:
        model = User
        fields = ["name", "email", "role", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "role": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if not email.endswith("@gmail.com"):
            raise forms.ValidationError("Enter a Gmail address ending with @gmail.com.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get("password")
        if new_password:
            user.set_password(new_password)  # hashed, never stored in plain text
        if commit:
            user.save()
        return user
