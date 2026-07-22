from django import forms

from .models import Course, Lesson
from accounts.models import User, UserRole


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            "title",
            "description",
            "thumbnail",
            "duration",
            "level",
            "instructor",
            "status",
            "is_premium",
            "price",
            "instructor_commission",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                }
            ),

            "thumbnail": forms.ClearableFileInput(
                attrs={"class": "form-control"}
            ),

            "duration": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "10 Hours",
                }
            ),

            "level": forms.Select(
                attrs={"class": "form-select"}
            ),

            "instructor": forms.Select(
                attrs={"class": "form-select"}
            ),

            "status": forms.Select(
                attrs={"class": "form-select"}
            ),

            "is_premium": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),

            "price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                }
            ),

            "instructor_commission": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show instructors in the dropdown, not students/admins
        self.fields["instructor"].queryset = User.objects.filter(role=UserRole.INSTRUCTOR)


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = [
            "title",
            "content",
            "video_url",
            "video",
            "notes",
            "resources",
            "order",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),

            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                }
            ),

            "video_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://youtube.com/...",
                }
            ),

            "video": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "video/*",
                }
            ),

            "notes": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".pdf",
                }
            ),

            "resources": forms.ClearableFileInput(
                attrs={"class": "form-control"}
            ),

            "order": forms.NumberInput(
                attrs={"class": "form-control"}
            ),
        }
