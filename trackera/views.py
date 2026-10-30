import logging
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

import errorutils

from .forms import ProjectForm, TaskForm, TimeLogForm, UserRegistrationForm
from .models import Project, Task, TimeLog
from .services import (
    calculate_dashboard_metrics,
    calculate_project_metrics,
    get_authorized_projects,
    get_authorized_tasks,
    record_time_log,
)

logger = logging.getLogger("trackera")


# ============================================================================
# AUTHENTICATION VIEWS
# ============================================================================

def register_view(request):
    """Register a new user account."""
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.set_password(form.cleaned_data["password"])
                user.save()
                messages.success(request, f"Account created successfully for {user.username}! You may now sign in.")
                return redirect("login")
            except Exception as e:
                errorutils.log_error(f"Registration failure for {form.cleaned_data.get('username')}: {e}")
                messages.error(request, "Failed to create account due to a system error.")
        else:
            messages.error(request, "Please correct the errors indicated below.")
    else:
        form = UserRegistrationForm()

    return render(request, "trackera/auth/register.html", {"form": form})


def login_view(request):
    """Sign in an existing user."""
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                next_url = request.GET.get("next") or request.POST.get("next")
                if next_url and next_url.startswith("/"):
                    return HttpResponseRedirect(next_url)
                return redirect("dashboard")
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid credentials. Please verify your details.")
    else:
        form = AuthenticationForm()

    return render(request, "trackera/auth/login.html", {"form": form})


@login_required
def logout_view(request):
    """Sign out the current user."""
    username = request.user.username
    logout(request)
    messages.info(request, f"You have been signed out. See you next time, {username}!")
    return redirect("login")


# ============================================================================
# DASHBOARD
# ============================================================================

@login_required
def dashboard_view(request):
    """Display system dashboard with live statistics computed via errorutils services."""
    try:
        stats = calculate_dashboard_metrics(request.user)
    except Exception as exc:
        errorutils.log_error(f"Dashboard calculation error for {request.user.username}: {exc}")
        stats = {}
        messages.error(request, "An error occurred while computing dashboard statistics.")

    return render(request, "trackera/dashboard.html", {"stats": stats})


# ============================================================================
# PROJECT CRUD
# ============================================================================

@login_required
def project_list_view(request):
    """List projects authorized for current user with search and status filtering."""
    projects = get_authorized_projects(request.user)

    # Search filter
    search_query = request.GET.get("q", "").strip()
    if search_query:
        projects = projects.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

    # Status filter
    status_filter = request.GET.get("status", "").strip()
    if status_filter:
        projects = projects.filter(status=status_filter)

    # Priority filter
    priority_filter = request.GET.get("priority", "").strip()
    if priority_filter:
        projects = projects.filter(priority=priority_filter)

    return render(
        request,
        "trackera/projects/project_list.html",
        {
            "projects": projects,
            "search_query": search_query,
            "selected_status": status_filter,
            "selected_priority": priority_filter,
            "status_choices": Project.STATUS_CHOICES,
            "priority_choices": Project.PRIORITY_CHOICES,
        },
    )


@login_required
def project_detail_view(request, pk):
    """Display details and metrics for a single project."""
    project = get_object_or_404(Project, pk=pk)

    # Authorization check
    if not request.user.is_superuser and project.owner != request.user:
        if not project.tasks.filter(assigned_to=request.user).exists():
            raise PermissionDenied("You are not authorized to view this project.")

    metrics = calculate_project_metrics(project)
    tasks = project.tasks.all()

    # Optional task filter within project
    status_filter = request.GET.get("task_status", "").strip()
    if status_filter:
        tasks = tasks.filter(status=status_filter)

    return render(
        request,
        "trackera/projects/project_detail.html",
        {
            "project": project,
            "metrics": metrics,
            "tasks": tasks,
            "selected_task_status": status_filter,
            "task_status_choices": Task.STATUS_CHOICES,
            "is_owner": project.owner == request.user or request.user.is_superuser,
        },
    )


@login_required
def project_create_view(request):
    """Create a new project owned by the current user."""
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            messages.success(request, f"Project '{project.title}' created successfully!")
            return redirect("project_detail", pk=project.pk)
        else:
            messages.error(request, "Failed to create project. Please check the errors.")
    else:
        form = ProjectForm()

    return render(
        request,
        "trackera/projects/project_form.html",
        {"form": form, "title": "Create New Project", "action_label": "Create Project"},
    )


@login_required
def project_update_view(request, pk):
    """Update an existing project (owner or superuser only)."""
    project = get_object_or_404(Project, pk=pk)

    # Authorization check: only owner or superuser
    if not request.user.is_superuser and project.owner != request.user:
        raise PermissionDenied("Only the project owner can edit project settings.")

    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f"Project '{project.title}' updated successfully!")
            return redirect("project_detail", pk=project.pk)
        else:
            messages.error(request, "Failed to update project. Please verify the form.")
    else:
        form = ProjectForm(instance=project)

    return render(
        request,
        "trackera/projects/project_form.html",
        {
            "form": form,
            "project": project,
            "title": f"Edit Project: {project.title}",
            "action_label": "Save Changes",
        },
    )


@login_required
def project_delete_view(request, pk):
    """Delete a project and all associated tasks (owner only)."""
    project = get_object_or_404(Project, pk=pk)

    if not request.user.is_superuser and project.owner != request.user:
        raise PermissionDenied("Only the project owner can delete this project.")

    if request.method == "POST":
        title = project.title
        project.delete()
        messages.success(request, f"Project '{title}' and all its tasks were deleted.")
        return redirect("project_list")

    return render(
        request,
        "trackera/projects/project_confirm_delete.html",
        {"project": project},
    )


# ============================================================================
# TASK CRUD
# ============================================================================

@login_required
def task_list_view(request):
    """List all tasks accessible to the user with multi-dimensional filtering."""
    tasks = get_authorized_tasks(request.user)

    # Filters
    search_query = request.GET.get("q", "").strip()
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

    project_id = request.GET.get("project", "").strip()
    if project_id.isdigit():
        tasks = tasks.filter(project_id=int(project_id))

    status_filter = request.GET.get("status", "").strip()
    if status_filter:
        tasks = tasks.filter(status=status_filter)

    priority_filter = request.GET.get("priority", "").strip()
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)

    assigned_filter = request.GET.get("assigned", "").strip()
    if assigned_filter == "me":
        tasks = tasks.filter(assigned_to=request.user)

    authorized_projects = get_authorized_projects(request.user)

    return render(
        request,
        "trackera/tasks/task_list.html",
        {
            "tasks": tasks,
            "projects": authorized_projects,
            "search_query": search_query,
            "selected_project": int(project_id) if project_id.isdigit() else "",
            "selected_status": status_filter,
            "selected_priority": priority_filter,
            "selected_assigned": assigned_filter,
            "status_choices": Task.STATUS_CHOICES,
            "priority_choices": Task.PRIORITY_CHOICES,
        },
    )


@login_required
def task_detail_view(request, pk):
    """View task details, logged hours, and form to add time log."""
    task = get_object_or_404(Task, pk=pk)

    # Authorization
    is_project_owner = task.project.owner == request.user or request.user.is_superuser
    is_assignee = task.assigned_to == request.user

    if not (is_project_owner or is_assignee):
        raise PermissionDenied("You do not have permission to view this task.")

    timelog_form = TimeLogForm()
    time_logs = task.time_logs.all()

    return render(
        request,
        "trackera/tasks/task_detail.html",
        {
            "task": task,
            "timelog_form": timelog_form,
            "time_logs": time_logs,
            "is_project_owner": is_project_owner,
            "is_assignee": is_assignee,
            "status_choices": Task.STATUS_CHOICES,
        },
    )


@login_required
def task_create_view(request, project_pk):
    """Create a new task inside a specific project (owner only)."""
    project = get_object_or_404(Project, pk=project_pk)

    if not request.user.is_superuser and project.owner != request.user:
        raise PermissionDenied("Only the project owner can add tasks to this project.")

    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.save()
            messages.success(request, f"Task '{task.title}' added to {project.title}!")
            return redirect("project_detail", pk=project.pk)
        else:
            messages.error(request, "Failed to create task. Please check the form errors.")
    else:
        form = TaskForm()

    return render(
        request,
        "trackera/tasks/task_form.html",
        {
            "form": form,
            "project": project,
            "title": f"Add Task to {project.title}",
            "action_label": "Create Task",
        },
    )


@login_required
def task_update_view(request, pk):
    """Update a task (project owner or assigned user)."""
    task = get_object_or_404(Task, pk=pk)

    is_owner = task.project.owner == request.user or request.user.is_superuser
    is_assignee = task.assigned_to == request.user

    if not (is_owner or is_assignee):
        raise PermissionDenied("You do not have permission to edit this task.")

    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, f"Task '{task.title}' updated successfully!")
            return redirect("task_detail", pk=task.pk)
        else:
            messages.error(request, "Failed to update task. Please verify your inputs.")
    else:
        form = TaskForm(instance=task)

    return render(
        request,
        "trackera/tasks/task_form.html",
        {
            "form": form,
            "task": task,
            "project": task.project,
            "title": f"Edit Task: {task.title}",
            "action_label": "Save Changes",
        },
    )


@login_required
def task_delete_view(request, pk):
    """Delete a task (project owner only)."""
    task = get_object_or_404(Task, pk=pk)

    if not request.user.is_superuser and task.project.owner != request.user:
        raise PermissionDenied("Only the project owner can delete tasks.")

    project_pk = task.project.pk
    if request.method == "POST":
        title = task.title
        task.delete()
        messages.success(request, f"Task '{title}' has been deleted.")
        return redirect("project_detail", pk=project_pk)

    return render(
        request,
        "trackera/tasks/task_confirm_delete.html",
        {"task": task, "project": task.project},
    )


@login_required
def task_update_status_quick_view(request, pk):
    """Quickly change the status of a task via POST (project owner or assignee)."""
    task = get_object_or_404(Task, pk=pk)

    is_owner = task.project.owner == request.user or request.user.is_superuser
    is_assignee = task.assigned_to == request.user

    if not (is_owner or is_assignee):
        raise PermissionDenied("You do not have permission to update this task status.")

    if request.method == "POST":
        new_status = request.POST.get("status")
        valid_statuses = [choice[0] for choice in Task.STATUS_CHOICES]
        if new_status in valid_statuses:
            task.status = new_status
            task.save()
            messages.success(request, f"Task status updated to '{task.get_status_display()}'.")
        else:
            messages.error(request, "Invalid status choice selected.")

    return redirect(request.META.get("HTTP_REFERER", reverse("task_detail", kwargs={"pk": task.pk})))


@login_required
def task_add_timelog_view(request, pk):
    """Add a work log to a task, utilizing errorutils for validation and logging."""
    task = get_object_or_404(Task, pk=pk)

    is_owner = task.project.owner == request.user or request.user.is_superuser
    is_assignee = task.assigned_to == request.user

    if not (is_owner or is_assignee):
        raise PermissionDenied("You do not have permission to log time on this task.")

    if request.method == "POST":
        form = TimeLogForm(request.POST)
        if form.is_valid():
            try:
                record_time_log(
                    task=task,
                    user=request.user,
                    hours=form.cleaned_data["hours_spent"],
                    notes=form.cleaned_data["notes"],
                    log_date=form.cleaned_data["log_date"],
                )
                messages.success(
                    request,
                    f"Successfully logged {form.cleaned_data['hours_spent']} hours for '{task.title}'!",
                )
            except errorutils.ValidationError as exc:
                messages.error(request, f"Validation failed: {exc}")
            except Exception as exc:
                errorutils.log_error(f"Failed to record time log on task {task.pk}: {exc}")
                messages.error(request, "Failed to record time log due to a system error.")
        else:
            messages.error(request, "Invalid time log entry. Check the form.")

    return redirect("task_detail", pk=task.pk)