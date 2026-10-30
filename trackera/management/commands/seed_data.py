import datetime
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
import errorutils
from trackera.models import Project, Task, TimeLog
from trackera.services import record_time_log


class Command(BaseCommand):
    help = "Seeds initial sample projects, tasks, time logs, and users for Trackera"

    def handle(self, *args, **options):
        self.stdout.write("Seeding sample data for Trackera...")

        # 1. Create or get demo users
        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@example.com", "first_name": "Admin", "last_name": "User", "is_staff": True, "is_superuser": True},
        )
        admin_user.set_password("admin123")
        admin_user.save()

        manager, _ = User.objects.get_or_create(
            username="sarah",
            defaults={"email": "sarah@example.com", "first_name": "Sarah", "last_name": "Chen"},
        )
        manager.set_password("password123")
        manager.save()

        dev, _ = User.objects.get_or_create(
            username="alex",
            defaults={"email": "alex@example.com", "first_name": "Alex", "last_name": "Rivers"},
        )
        dev.set_password("password123")
        dev.save()

        today = timezone.now().date()

        # 2. Project 1: Cloud Migration & Security
        p1, _ = Project.objects.get_or_create(
            title="Cloud Infrastructure Migration",
            owner=manager,
            defaults={
                "description": "Migrate core microservices from legacy on-premise hosts to scalable AWS containers.",
                "status": "in_progress",
                "priority": "high",
                "budget": Decimal("25000.00"),
                "start_date": today - datetime.timedelta(days=20),
                "end_date": today + datetime.timedelta(days=40),
            },
        )

        # 3. Project 2: Customer Portal Revamp
        p2, _ = Project.objects.get_or_create(
            title="Customer Portal & Billing Dashboard",
            owner=manager,
            defaults={
                "description": "Redesign self-service billing, invoice generation, and account profile management with Outfit design system.",
                "status": "planning",
                "priority": "medium",
                "budget": Decimal("14500.00"),
                "start_date": today - datetime.timedelta(days=5),
                "end_date": today + datetime.timedelta(days=60),
            },
        )

        # 4. Project 3: Internal ERP Integration
        p3, _ = Project.objects.get_or_create(
            title="Internal Inventory ERP Integration",
            owner=manager,
            defaults={
                "description": "Sync real-time warehouse stock counts with e-commerce store catalog.",
                "status": "completed",
                "priority": "medium",
                "budget": Decimal("8000.00"),
                "start_date": today - datetime.timedelta(days=60),
                "end_date": today - datetime.timedelta(days=10),
            },
        )

        # 5. Create Tasks for Project 1
        t1, _ = Task.objects.get_or_create(
            project=p1,
            title="Terraform Infrastructure Provisioning",
            defaults={
                "description": "Configure VPC, subnets, NAT gateways, and ECS clusters using Infrastructure as Code.",
                "assigned_to": dev,
                "status": "completed",
                "priority": "high",
                "estimated_hours": 16.0,
                "due_date": today - datetime.timedelta(days=5),
            },
        )

        t2, _ = Task.objects.get_or_create(
            project=p1,
            title="Database Replication & Failover Testing",
            defaults={
                "description": "Configure multi-region PostgreSQL read replicas and conduct automated failover drills.",
                "assigned_to": dev,
                "status": "in_progress",
                "priority": "urgent",
                "estimated_hours": 24.0,
                "due_date": today + datetime.timedelta(days=4),
            },
        )

        t3, _ = Task.objects.get_or_create(
            project=p1,
            title="CI/CD Pipeline Security Hardening",
            defaults={
                "description": "Audit GitHub Actions runner permissions and integrate static container vulnerability scanners.",
                "assigned_to": manager,
                "status": "todo",
                "priority": "medium",
                "estimated_hours": 12.0,
                "due_date": today + datetime.timedelta(days=14),
            },
        )

        # 6. Tasks for Project 2
        t4, _ = Task.objects.get_or_create(
            project=p2,
            title="User Onboarding & Profile Flow Wireframes",
            defaults={
                "description": "Design responsive views adhering to Outfit typography and light-green aesthetics.",
                "assigned_to": dev,
                "status": "review",
                "priority": "high",
                "estimated_hours": 18.0,
                "due_date": today + datetime.timedelta(days=7),
            },
        )

        t5, _ = Task.objects.get_or_create(
            project=p2,
            title="Invoice PDF Download Service",
            defaults={
                "description": "Generate receipt statements securely for past payment cycles.",
                "assigned_to": dev,
                "status": "todo",
                "priority": "low",
                "estimated_hours": 8.0,
                "due_date": today + datetime.timedelta(days=25),
            },
        )

        # 7. Record Time Logs using record_time_log (verified via errorutils)
        if not t1.time_logs.exists():
            record_time_log(t1, dev, 8.0, "Wrote initial Terraform modules for VPC and ECS", today - datetime.timedelta(days=8))
            record_time_log(t1, dev, 8.5, "Completed cluster validation and automated state lock", today - datetime.timedelta(days=6))

        if not t2.time_logs.exists():
            record_time_log(t2, dev, 6.0, "Configured PostgreSQL streaming replication", today - datetime.timedelta(days=2))
            record_time_log(t2, manager, 2.0, "Code review and failover runbook verification", today - datetime.timedelta(days=1))

        self.stdout.write(self.style.SUCCESS("Successfully seeded Trackera database!"))
        self.stdout.write("Created users: 'admin' (password: admin123), 'sarah' (password: password123), 'alex' (password: password123)")
