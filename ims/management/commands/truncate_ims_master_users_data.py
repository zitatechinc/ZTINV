from django.core.management.base import BaseCommand
from accounts.models import User
from ims.models import (
    UserReg, Manager, Director,
    Units, Stages, Roles, Designation, Department,
    TenderType, ProcurementType, SourceOfMake, Delivery
)


class Command(BaseCommand):
    help = "Safely truncate IMS + Users tables respecting FK constraints"

    def truncate(self, model, name):
        count = model.objects.count()
        model.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(
            f"{name} truncated successfully ({count} records deleted)"
        ))

    def handle(self, *args, **kwargs):

        # ---------- CHILD TABLES FIRST ----------
        self.truncate(UserReg, "UserReg")
        self.truncate(Director, "Director")
        self.truncate(Manager, "Manager")

        # ---------- MASTER DEPENDENCIES ----------
        self.truncate(Roles, "Roles")
        self.truncate(Designation, "Designation")
        self.truncate(Department, "Department")

        # ---------- INVENTORY MASTERS ----------
        self.truncate(Delivery, "Delivery")
        self.truncate(SourceOfMake, "SourceOfMake")
        self.truncate(ProcurementType, "ProcurementType")
        self.truncate(TenderType, "TenderType")
        self.truncate(Stages, "Stages")
        self.truncate(Units, "Units")

        # ---------- USERS LAST ----------
        self.truncate(User, "accounts.User")

        self.stdout.write(self.style.SUCCESS(
            "\nALL TABLES TRUNCATED SUCCESSFULLY\n"
        ))
