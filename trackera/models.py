import errorutils
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models
from django.utils import timezone


class BaseAuditedModel(models.Model):
    """Abstract base model that provides timestamp auditing fields."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseProjectEntity(BaseAuditedModel):
    """Abstract base model for named entities in the project management system."""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")

    class Meta:
        abstract = True

    def __str__(self):
        return self.title


class Project(BaseProjectEntity):
    """Project model owned by a user."""
    STATUS_CHOICES = [
        ("planning", "Planning"),
        ("in_progress", "In Progress"),
        ("on_hold", "On Hold"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_projects",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="planning",
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="medium",
    )
    budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        super().clean()
        # Use errorutils.check_not_none to verify owner if set
        if self.owner_id is not None:
            try:
                errorutils.check_not_none(self.owner, name="Project owner")
            except errorutils.ValidationError as exc:
                raise DjangoValidationError({"owner": str(exc)})

        # Validate budget with errorutils.validate_number
        if self.budget is not None:
            try:
                numeric_budget = errorutils.validate_number(float(self.budget), name="budget")
                if numeric_budget < 0:
                    raise DjangoValidationError({"budget": "Budget cannot be negative."})
            except errorutils.ValidationError as exc:
                raise DjangoValidationError({"budget": str(exc)})

        # Ensure end_date is after start_date
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise DjangoValidationError({"end_date": "End date cannot precede the start date."})

    @property
    def total_tasks_count(self) -> int:
        return self.tasks.count()

    @property
    def completed_tasks_count(self) -> int:
        return self.tasks.filter(status="completed").count()

    @property
    def completion_percentage(self) -> float:
        total = self.total_tasks_count
        if total == 0:
            return 100.0 if self.status == "completed" else 0.0
        return round((self.completed_tasks_count / total) * 100.0, 1)

    @property
    def total_estimated_hours(self) -> float:
        tasks = list(self.tasks.all())
        total = 0.0
        for task in tasks:
            total = errorutils.ops.add(total, task.estimated_hours)
        return round(total, 2)

    @property
    def total_logged_hours(self) -> float:
        total = 0.0
        for task in self.tasks.all():
            total = errorutils.ops.add(total, task.total_logged_hours)
        return round(total, 2)


class Task(BaseProjectEntity):
    """Task model linked to a Project and optionally assigned to a User."""
    STATUS_CHOICES = [
        ("todo", "To Do"),
        ("in_progress", "In Progress"),
        ("review", "In Review"),
        ("completed", "Completed"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="todo",
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="medium",
    )
    estimated_hours = models.FloatField(default=0.0)
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["due_date", "-priority", "-created_at"]

    def clean(self):
        super().clean()
        # Use errorutils.validate_number to validate estimated_hours
        try:
            val = errorutils.validate_number(self.estimated_hours, name="estimated_hours")
            if val < 0:
                raise DjangoValidationError({"estimated_hours": "Estimated hours cannot be negative."})
        except errorutils.ValidationError as exc:
            raise DjangoValidationError({"estimated_hours": str(exc)})

    @property
    def total_logged_hours(self) -> float:
        logs = self.time_logs.all()
        total = 0.0
        for log in logs:
            total = errorutils.ops.add(total, log.hours_spent)
        return round(total, 2)

    @property
    def is_overdue(self) -> bool:
        if self.due_date and self.status != "completed":
            return self.due_date < timezone.now().date()
        return False


class TimeLog(BaseAuditedModel):
    """Work log entry tracking hours spent on a specific task."""
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="time_logs",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="time_logs",
    )
    hours_spent = models.FloatField()
    log_date = models.DateField(default=timezone.now)
    notes = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-log_date", "-created_at"]

    def clean(self):
        super().clean()
        # Validate hours_spent using errorutils.validate_number
        try:
            val = errorutils.validate_number(self.hours_spent, name="hours_spent")
            if val <= 0:
                raise DjangoValidationError({"hours_spent": "Logged hours must be greater than zero."})
        except errorutils.ValidationError as exc:
            raise DjangoValidationError({"hours_spent": str(exc)})

        # Validate task and user using errorutils.check_not_none
        if self.task_id is not None:
            try:
                errorutils.check_not_none(self.task, name="Task")
            except errorutils.ValidationError as exc:
                raise DjangoValidationError({"task": str(exc)})

        if self.user_id is not None:
            try:
                errorutils.check_not_none(self.user, name="User")
            except errorutils.ValidationError as exc:
                raise DjangoValidationError({"user": str(exc)})

    def __str__(self):
        return f"{self.user.username} logged {self.hours_spent}h on {self.task.title}"
