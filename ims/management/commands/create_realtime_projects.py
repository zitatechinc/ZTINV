import random
from django.core.management.base import BaseCommand
from django.utils.timezone import now
from ims.models import Project, BudgetAllocation


class Command(BaseCommand):
    help = "Create 10 realtime projects with realistic names and budgets"

    def handle(self, *args, **kwargs):

        current_year = now().year
        financial_year = f"{current_year}-{current_year + 1}"

        project_names = [
            "Office Infrastructure Upgrade",
            "Warehouse Expansion Phase 1",
            "ERP Implementation",
            "Manufacturing Line Setup",
            "IT Hardware Procurement",
            "Logistics Optimization",
            "Quality Lab Modernization",
            "Retail Store Setup",
            "Data Center Upgrade",
            "Plant Maintenance Project"
        ]

        created_count = 0

        for i in range(10):

            project_code = f"PR{i+1}"     # PR1, PR2...
            project_name = f"project_{i+1}"

            project, created = Project.objects.get_or_create(
                project_id=project_code,
                defaults={"name": project_name}
            )

            if created:
                created_count += 1

                allocated_amount = random.choice(range(10000000, 50000001, 5000000))

                BudgetAllocation.objects.get_or_create(
                    project=project,
                    financial_year=financial_year,
                    defaults={
                        "allocated_budget": allocated_amount,
                        "remaining_budget": allocated_amount,
                        "budgettype": "Project"
                    }
                )

        self.stdout.write(self.style.SUCCESS(
            f"{created_count} Realtime Projects Created Successfully!"
        ))
