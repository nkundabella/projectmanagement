"""
Reusable business logic and analytics services for Trackera Project Management.
Integrates errorutils for safe computations, numeric validations, and resilient metrics.
"""
from typing import Any, Dict, List, Optional
import errorutils
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.utils import timezone

from .models import Project, Task, TimeLog


def compute_average_safe(numbers: List[float], default: float = 0.0) -> float:
    """Safely calculate the average of numbers using errorutils.ops.average and safe_call."""
    if not numbers:
        return default
    result = errorutils.safe_call(errorutils.ops.average, numbers, default=default)
    return round(result if result is not None else default, 2)


def calculate_project_metrics(project: Project, standard_hourly_rate: float = 45.0) -> Dict[str, Any]:
    """
    Calculate detailed metrics for a specific project.
    Leverages errorutils for robust numeric operations and error handling.
    """
    tasks = list(project.tasks.all())
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.status == "completed")
    in_progress_tasks = sum(1 for t in tasks if t.status == "in_progress")
    todo_tasks = sum(1 for t in tasks if t.status == "todo")
    review_tasks = sum(1 for t in tasks if t.status == "review")

    # Extract task estimated hours
    est_hours_list = [t.estimated_hours for t in tasks if t.estimated_hours is not None]
    avg_estimated_hours = compute_average_safe(est_hours_list, default=0.0)

    # Accumulate total estimated hours using errorutils.ops.add
    total_estimated_hours = 0.0
    for h in est_hours_list:
        total_estimated_hours = errorutils.ops.add(total_estimated_hours, h)

    # Accumulate total logged hours
    total_logged_hours = 0.0
    for t in tasks:
        total_logged_hours = errorutils.ops.add(total_logged_hours, t.total_logged_hours)

    # Projected cost calculation using errorutils.ops.multiply
    def _calc_projected_cost():
        rate = errorutils.validate_number(standard_hourly_rate, "standard_hourly_rate")
        return errorutils.ops.multiply(total_logged_hours, rate)

    projected_labor_cost = errorutils.safe_call(_calc_projected_cost, default=0.0)

    # Overdue tasks
    today = timezone.now().date()
    overdue_tasks = sum(
        1 for t in tasks if t.due_date and t.status != "completed" and t.due_date < today
    )

    completion_percentage = (
        round((completed_tasks / total_tasks) * 100.0, 1) if total_tasks > 0 else (100.0 if project.status == "completed" else 0.0)
    )

    budget_val = float(project.budget) if project.budget else 0.0
    budget_variance = budget_val - projected_labor_cost

    return {
        "project": project,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "in_progress_tasks": in_progress_tasks,
        "todo_tasks": todo_tasks,
        "review_tasks": review_tasks,
        "overdue_tasks": overdue_tasks,
        "completion_percentage": completion_percentage,
        "total_estimated_hours": round(total_estimated_hours, 2),
        "total_logged_hours": round(total_logged_hours, 2),
        "avg_estimated_hours": avg_estimated_hours,
        "projected_labor_cost": round(projected_labor_cost, 2),
        "budget_variance": round(budget_variance, 2),
        "is_over_budget": projected_labor_cost > budget_val if budget_val > 0 else False,
    }


def get_authorized_projects(user: User) -> QuerySet:
    """Return projects that the user owns or is assigned to tasks in."""
    if user.is_superuser:
        return Project.objects.all().distinct()
    return Project.objects.filter(owner=user).distinct()


def get_authorized_tasks(user: User) -> QuerySet:
    """Return tasks that belong to projects the user owns or are directly assigned to the user."""
    if user.is_superuser:
        return Task.objects.all().distinct()
    return Task.objects.filter(
        models_q_filter(user)
    ).distinct()


def models_q_filter(user: User):
    from django.db.models import Q
    return Q(project__owner=user) | Q(assigned_to=user)


def calculate_dashboard_metrics(user: User) -> Dict[str, Any]:
    """
    Generate comprehensive dashboard statistics for the logged-in user.
    Uses errorutils for arithmetic aggregation and error-proof fallbacks.
    """
    projects = get_authorized_projects(user)
    tasks = get_authorized_tasks(user)

    total_projects = projects.count()
    active_projects = projects.filter(status__in=["planning", "in_progress"]).count()
    completed_projects = projects.filter(status="completed").count()

    # Collect project budgets for average calculation
    budgets = [float(p.budget) for p in projects if p.budget and float(p.budget) > 0]
    avg_budget = compute_average_safe(budgets, default=0.0)

    # Accumulate total budget using errorutils.ops.add
    total_budget = 0.0
    for b in budgets:
        total_budget = errorutils.ops.add(total_budget, b)

    total_tasks = tasks.count()
    todo_tasks = tasks.filter(status="todo").count()
    in_progress_tasks = tasks.filter(status="in_progress").count()
    review_tasks = tasks.filter(status="review").count()
    completed_tasks = tasks.filter(status="completed").count()

    today = timezone.now().date()
    overdue_tasks = tasks.filter(due_date__lt=today).exclude(status="completed").count()

    task_estimates = [t.estimated_hours for t in tasks if t.estimated_hours is not None]
    avg_task_estimate = compute_average_safe(task_estimates, default=0.0)

    # Compute overall completion rate
    overall_completion_rate = (
        round((completed_tasks / total_tasks) * 100.0, 1) if total_tasks > 0 else 0.0
    )

    # Time logs aggregated
    user_time_logs = TimeLog.objects.filter(user=user)
    total_user_logged_hours = 0.0
    for log in user_time_logs:
        total_user_logged_hours = errorutils.ops.add(total_user_logged_hours, log.hours_spent)

    return {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "completed_projects": completed_projects,
        "total_budget": round(total_budget, 2),
        "avg_budget": avg_budget,
        "total_tasks": total_tasks,
        "todo_tasks": todo_tasks,
        "in_progress_tasks": in_progress_tasks,
        "review_tasks": review_tasks,
        "completed_tasks": completed_tasks,
        "overdue_tasks": overdue_tasks,
        "avg_task_estimate": avg_task_estimate,
        "overall_completion_rate": overall_completion_rate,
        "total_user_logged_hours": round(total_user_logged_hours, 2),
        "recent_projects": projects[:5],
        "urgent_tasks": tasks.filter(priority__in=["urgent", "high"]).exclude(status="completed")[:5],
    }


def record_time_log(task: Task, user: User, hours: float, notes: str = "", log_date=None) -> TimeLog:
    """
    Create a TimeLog entry with strict validation through errorutils.
    """
    errorutils.check_not_none(task, "task")
    errorutils.check_not_none(user, "user")
    validated_hours = errorutils.validate_number(hours, "hours")

    if validated_hours <= 0:
        raise errorutils.ValidationError("Logged hours must be strictly positive.")

    date_to_use = log_date or timezone.now().date()
    log = TimeLog.objects.create(
        task=task,
        user=user,
        hours_spent=validated_hours,
        notes=notes.strip() if notes else "",
        log_date=date_to_use,
    )
    return log
