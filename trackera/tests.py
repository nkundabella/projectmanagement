import datetime
from decimal import Decimal
import errorutils
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import BaseAuditedModel, BaseProjectEntity, Project, Task, TimeLog
from .services import (
    calculate_dashboard_metrics,
    calculate_project_metrics,
    compute_average_safe,
    get_authorized_projects,
    get_authorized_tasks,
    record_time_log,
)


class ErrorUtilsIntegrationTest(TestCase):
    """Verify that errorutils functions and operations behave as expected in the system."""

    def test_validate_number_success(self):
        self.assertEqual(errorutils.validate_number(10), 10.0)
        self.assertEqual(errorutils.validate_number(12.5), 12.5)
        self.assertEqual(errorutils.validate_number(0), 0.0)

    def test_validate_number_rejects_bool_and_non_numbers(self):
        with self.assertRaises(errorutils.ValidationError):
            errorutils.validate_number(True)
        with self.assertRaises(errorutils.ValidationError):
            errorutils.validate_number("abc")
        with self.assertRaises(errorutils.ValidationError):
            errorutils.validate_number(float("inf"))
        with self.assertRaises(errorutils.ValidationError):
            errorutils.validate_number(float("nan"))

    def test_check_not_none(self):
        self.assertEqual(errorutils.check_not_none("Valid"), "Valid")
        with self.assertRaises(errorutils.ValidationError):
            errorutils.check_not_none(None, "sample_field")

    def test_ops_add_and_multiply(self):
        self.assertEqual(errorutils.ops.add(5.5, 4.5), 10.0)
        self.assertEqual(errorutils.ops.multiply(8.0, 50.0), 400.0)

    def test_ops_average_and_safe_fallback(self):
        numbers = [10.0, 20.0, 30.0]
        self.assertEqual(errorutils.ops.average(numbers), 20.0)
        # Empty list raises ValueError in errorutils, compute_average_safe safely returns fallback
        self.assertEqual(compute_average_safe([], default=0.0), 0.0)


class ModelAndInheritanceTest(TestCase):
    """Test model inheritance, field properties, and model validation with errorutils."""

    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="alicepassword123")

    def test_model_inheritance(self):
        self.assertTrue(issubclass(Project, BaseProjectEntity))
        self.assertTrue(issubclass(Project, BaseAuditedModel))
        self.assertTrue(issubclass(Task, BaseProjectEntity))
        self.assertTrue(issubclass(TimeLog, BaseAuditedModel))

    def test_project_clean_validates_budget_using_errorutils(self):
        # Negative budget should trigger DjangoValidationError via errorutils check
        project = Project(
            owner=self.user,
            title="Website Revamp",
            budget=Decimal("-500.00"),
        )
        with self.assertRaises(DjangoValidationError):
            project.clean()

    def test_task_clean_validates_estimated_hours(self):
        project = Project.objects.create(
            owner=self.user,
            title="Website Revamp",
            budget=Decimal("5000.00"),
        )
        task = Task(
            project=project,
            title="Design Mockups",
            estimated_hours=-4.0,
        )
        with self.assertRaises(DjangoValidationError):
            task.clean()

    def test_completion_percentage_calculation(self):
        project = Project.objects.create(owner=self.user, title="ERP Migration")
        Task.objects.create(project=project, title="T1", status="completed")
        Task.objects.create(project=project, title="T2", status="in_progress")
        Task.objects.create(project=project, title="T3", status="todo")

        self.assertEqual(project.total_tasks_count, 3)
        self.assertEqual(project.completed_tasks_count, 1)
        self.assertEqual(project.completion_percentage, 33.3)


class ServicesBusinessLogicTest(TestCase):
    """Test reusable business logic and services powered by errorutils."""

    def setUp(self):
        self.user = User.objects.create_user(username="bob", password="bobpassword123")
        self.project = Project.objects.create(
            owner=self.user,
            title="Mobile Application",
            budget=Decimal("10000.00"),
        )
        self.t1 = Task.objects.create(
            project=self.project,
            title="API Setup",
            estimated_hours=10.0,
            status="completed",
        )
        self.t2 = Task.objects.create(
            project=self.project,
            title="UI Screens",
            estimated_hours=20.0,
            status="in_progress",
        )

    def test_calculate_project_metrics(self):
        record_time_log(task=self.t1, user=self.user, hours=8.5, notes="Initial API endpoints")
        record_time_log(task=self.t2, user=self.user, hours=4.5, notes="Wireframes")

        metrics = calculate_project_metrics(self.project, standard_hourly_rate=50.0)
        self.assertEqual(metrics["total_tasks"], 2)
        self.assertEqual(metrics["completed_tasks"], 1)
        self.assertEqual(metrics["completion_percentage"], 50.0)
        self.assertEqual(metrics["total_estimated_hours"], 30.0)
        self.assertEqual(metrics["total_logged_hours"], 13.0)
        self.assertEqual(metrics["avg_estimated_hours"], 15.0)
        # 13.0 hours * $50/hr = $650
        self.assertEqual(metrics["projected_labor_cost"], 650.0)
        self.assertEqual(metrics["budget_variance"], 9350.0)

    def test_dashboard_metrics(self):
        metrics = calculate_dashboard_metrics(self.user)
        self.assertEqual(metrics["total_projects"], 1)
        self.assertEqual(metrics["active_projects"], 1)
        self.assertEqual(metrics["total_tasks"], 2)
        self.assertEqual(metrics["completed_tasks"], 1)
        self.assertEqual(metrics["avg_budget"], 10000.0)


class SecurityAndAuthorizationTest(TestCase):
    """Verify that users can only access and modify records they are authorized to manage."""

    def setUp(self):
        self.user1 = User.objects.create_user(username="carol", password="carolpassword123")
        self.user2 = User.objects.create_user(username="david", password="davidpassword123")

        self.project_carol = Project.objects.create(
            owner=self.user1,
            title="Carol's Secret Project",
            budget=Decimal("2000.00"),
        )
        self.task_carol = Task.objects.create(
            project=self.project_carol,
            title="Secret Task",
            estimated_hours=5.0,
        )

        self.client_david = Client()
        self.client_david.login(username="david", password="davidpassword123")

    def test_unauthorized_user_cannot_view_or_edit_project(self):
        # David cannot view Carol's project details
        response = self.client_david.get(reverse("project_detail", kwargs={"pk": self.project_carol.pk}))
        self.assertEqual(response.status_code, 403)

        # David cannot edit Carol's project
        response = self.client_david.get(reverse("project_update", kwargs={"pk": self.project_carol.pk}))
        self.assertEqual(response.status_code, 403)

        # David cannot delete Carol's project
        response = self.client_david.post(reverse("project_delete", kwargs={"pk": self.project_carol.pk}))
        self.assertEqual(response.status_code, 403)

    def test_authorized_owner_can_manage_project(self):
        client_carol = Client()
        client_carol.login(username="carol", password="carolpassword123")

        # Carol can view her project
        response = client_carol.get(reverse("project_detail", kwargs={"pk": self.project_carol.pk}))
        self.assertEqual(response.status_code, 200)

        # Carol can update her project
        response = client_carol.post(
            reverse("project_update", kwargs={"pk": self.project_carol.pk}),
            {
                "title": "Carol's Updated Project",
                "status": "in_progress",
                "priority": "high",
                "budget": "3500.00",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.project_carol.refresh_from_db()
        self.assertEqual(self.project_carol.title, "Carol's Updated Project")
        self.assertEqual(self.project_carol.budget, Decimal("3500.00"))