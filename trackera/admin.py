from django.contrib import admin
from .models import Project, Task, TimeLog


class TaskInline(admin.TabularInline):
    model = Task
    extra = 1
    fields = ("title", "assigned_to", "status", "priority", "estimated_hours", "due_date")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "status", "priority", "budget", "completion_percentage", "created_at")
    list_filter = ("status", "priority", "created_at")
    search_fields = ("title", "description", "owner__username")
    inlines = [TaskInline]


class TimeLogInline(admin.TabularInline):
    model = TimeLog
    extra = 1
    fields = ("user", "hours_spent", "log_date", "notes")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "assigned_to", "status", "priority", "estimated_hours", "due_date")
    list_filter = ("status", "priority", "project")
    search_fields = ("title", "description", "project__title", "assigned_to__username")
    inlines = [TimeLogInline]


@admin.register(TimeLog)
class TimeLogAdmin(admin.ModelAdmin):
    list_display = ("task", "user", "hours_spent", "log_date", "created_at")
    list_filter = ("log_date", "user")
    search_fields = ("task__title", "user__username", "notes")