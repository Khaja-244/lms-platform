from django import forms

from .models import Subscription


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = [
            "user",
            "plan",
            "start_date",
            "end_date",
            "status",
        ]
        widgets = {
            "user": forms.Select(attrs={"class": "form-select"}),
            "plan": forms.Select(attrs={"class": "form-select"}),
            "start_date": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "end_date": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }


