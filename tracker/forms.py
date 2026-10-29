from django import forms
from django.utils import timezone

from .models import Assignment, Subject


class StyledModelForm(forms.ModelForm):
    """Adds a CSS class to every widget so the stylesheet can style it."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " form-control").strip()


class AssignmentForm(StyledModelForm):
    class Meta:
        model = Assignment
        fields = ["title", "subject", "description", "due_date", "priority", "status"]
        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "e.g. Data Structures - Lab Report 3"}
            ),
            "description": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Notes, topics, submission format..."}
            ),
            "due_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if len(title) < 3:
            raise forms.ValidationError("Title must be at least 3 characters long.")
        return title

    def clean_due_date(self):
        due = self.cleaned_data["due_date"]
        # A NEW assignment cannot have a deadline in the past.
        # When editing, past dates are allowed so overdue work can be recorded.
        if not self.instance.pk and due < timezone.localdate():
            raise forms.ValidationError("Due date cannot be in the past.")
        return due


class SubjectForm(StyledModelForm):
    class Meta:
        model = Subject
        fields = ["name", "code"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. Python Programming"}),
            "code": forms.TextInput(attrs={"placeholder": "e.g. CS101 (optional)"}),
        }

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if Subject.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("A subject with this name already exists.")
        return name
