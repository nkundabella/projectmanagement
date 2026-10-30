import errorutils
from django import forms
from django.contrib.auth.models import User
from .models import Project, Task, TimeLog


class ProjectForm(forms.ModelForm):
    """Form to create or update a Project."""

    class Meta:
        model = Project
        fields = ["title", "description", "status", "priority", "budget", "start_date", "end_date"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter project title"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Describe project goals, scope, and objectives..."}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "priority": forms.Select(attrs={"class": "form-control"}),
            "budget": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "0.00"}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }

    def clean_budget(self):
        budget_val = self.cleaned_data.get("budget")
        if budget_val is not None:
            try:
                # Use errorutils.validate_number to strictly validate the number
                validated = errorutils.validate_number(float(budget_val), name="budget")
                if validated < 0:
                    raise forms.ValidationError("Budget cannot be negative.")
                return budget_val
            except errorutils.ValidationError as exc:
                raise forms.ValidationError(str(exc))
        return budget_val

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date and end_date < start_date:
            self.add_error("end_date", "End date cannot be earlier than start date.")
        return cleaned_data


class TaskForm(forms.ModelForm):
    """Form to create or update a Task."""

    class Meta:
        model = Task
        fields = ["title", "description", "assigned_to", "status", "priority", "estimated_hours", "due_date"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Task title"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Task details, acceptance criteria..."}),
            "assigned_to": forms.Select(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "priority": forms.Select(attrs={"class": "form-control"}),
            "estimated_hours": forms.NumberInput(attrs={"class": "form-control", "step": "0.25", "min": "0"}),
            "due_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = User.objects.filter(is_active=True).order_by("username")
        self.fields["assigned_to"].empty_label = "-- Unassigned --"

    def clean_estimated_hours(self):
        hours = self.cleaned_data.get("estimated_hours")
        if hours is not None:
            try:
                validated = errorutils.validate_number(hours, name="estimated_hours")
                if validated < 0:
                    raise forms.ValidationError("Estimated hours cannot be negative.")
                return validated
            except errorutils.ValidationError as exc:
                raise forms.ValidationError(str(exc))
        return 0.0


class TimeLogForm(forms.ModelForm):
    """Form to record time spent on a task."""

    class Meta:
        model = TimeLog
        fields = ["hours_spent", "log_date", "notes"]
        widgets = {
            "hours_spent": forms.NumberInput(attrs={"class": "form-control", "step": "0.25", "min": "0.1", "placeholder": "e.g. 2.5"}),
            "log_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "notes": forms.TextInput(attrs={"class": "form-control", "placeholder": "What did you work on?"}),
        }

    def clean_hours_spent(self):
        hours = self.cleaned_data.get("hours_spent")
        if hours is not None:
            try:
                validated = errorutils.validate_number(hours, name="hours_spent")
                if validated <= 0:
                    raise forms.ValidationError("Logged hours must be greater than zero.")
                return validated
            except errorutils.ValidationError as exc:
                raise forms.ValidationError(str(exc))
        return hours


class UserRegistrationForm(forms.ModelForm):
    """Form for registering a new user."""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"}),
        min_length=6,
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirm password"}),
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "placeholder": "Username"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email address"}),
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "First name"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Last name"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        pwd = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")
        if pwd and confirm and pwd != confirm:
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned_data
