from django.core.management.base import BaseCommand
from ims.models import (
    Units, Stages, Roles, Designation, Department,
    TenderType, ProcurementType, SourceOfMake, Delivery
)
from django.db import transaction

class Command(BaseCommand):
    help = "Seed all inventory master data"

    def handle(self, *args, **kwargs):

        # Helper for printing status
        def msg(model, created):
            total = model.objects.count()
            if created > 0:
                return f"{created} rows injected (Total: {total})"
            return f"0 already injected (Total: {total})"

        # ================= PROCUREMENT TYPES =================
        procurement_types = [
            ("01", "Capital"),
            ("02", "Revenue"),
            ("03", "Mixed"),
        ]

        procurement_created = 0
        for code, name in procurement_types:
            _, created = ProcurementType.objects.get_or_create(
                Procurement_code=code,
                defaults={"Procurement_name": name}
            )
            if created:
                procurement_created += 1

        # ================= DEPARTMENTS =================
        departments_list = [
            ("Engineering", "01"),
            ("Stores", "02"),
            ("Purchase", "03"),
            ("Warehouse", "04"),
            ("Sales", "05"),
            ("Accounts", "06"),
            ("Quality Control", "07"),
            ("Maintenance", "08"),
            ("Administration", "09"),
            ("IT Support", "10")
        ]

        department_created = 0

        with transaction.atomic():
            for name, code in departments_list:

                obj = Department.objects.filter(dept_code=code).first()

                if obj:
                    # Only update name if NOT used elsewhere
                    if obj.dept_name != name and not Department.objects.filter(dept_name=name).exclude(pk=obj.pk).exists():
                        obj.dept_name = name
                        obj.save(update_fields=["dept_name"])

                else:
                    # Create only if name ALSO doesn't exist
                    if not Department.objects.filter(dept_name=name).exists():
                        Department.objects.create(dept_code=code, dept_name=name)
                        department_created += 1

        # ================= SOURCE OF MAKE =================
        source_types = [
            ("01", "Indigenous"),
            ("02", "Imported"),
        ]

        source_created = 0
        for code, name in source_types:
            _, created = SourceOfMake.objects.get_or_create(
                source_code=code,
                defaults={"source_type": name}
            )
            if created:
                source_created += 1

        # ================= TENDER TYPES =================
        tender_types = [
            ("01", "Open"),
            ("02", "Limited"),
            ("03", "Single"),
            ("04", "Proprietary"),
            ("05", "Global"),
        ]

        tender_created = 0
        for code, name in tender_types:
            _, created = TenderType.objects.get_or_create(
                tender_code=code,
                defaults={"tender_type": name}
            )
            if created:
                tender_created += 1

        # ================= UNITS =================
        units_list = [
            "pcs", "kg", "g", "mg", "ton",
            "ltr", "ml",
            "m", "cm", "mm",
            "sqft", "sqm",
            "box", "pack", "bag",
            "roll", "bundle",
            "set", "pair",
            "dozen"
        ]

        units_created = 0
        for unit in units_list:
            _, created = Units.objects.get_or_create(unit=unit)
            if created:
                units_created += 1

        # ================= DELIVERY TYPES =================
        delivery_types = [
            "Full Quantity",
            "Staggered",
            "Partial",
            "Express Delivery",
            "Scheduled Delivery",
            "Same Day Delivery",
            "Next Day Delivery",
            "Bulk Delivery",
            "Split Shipment",
            "Dropship",
        ]

        delivery_created = 0
        for name in delivery_types:
            _, created = Delivery.objects.get_or_create(delivery_name=name)
            if created:
                delivery_created += 1

        # ================= STAGES =================
        stages_list = [
            "stage1", "stage2", "stage3", "stage4", "stage5",
            "stage6", "stage7", "stage8", "stage9",
            "stage10", "stage11"
        ]

        stages_created = 0
        for stage in stages_list:
            _, created = Stages.objects.get_or_create(stage=stage)
            if created:
                stages_created += 1

        # ================= ROLES =================
        roles_list = [
            "Indentor",
            "Recommending Authority",
            "IMM",
            "Accounts",
            "Approving Authority"
        ]

        roles_created = 0
        for role in roles_list:
            _, created = Roles.objects.get_or_create(role=role)
            if created:
                roles_created += 1

        # ================= DESIGNATIONS =================
        designation_list = [
            "Store Manager",
            "Purchase Officer",
            "Warehouse Supervisor",
            "Inventory Executive",
            "Accounts Officer",
            "Quality Inspector",
            "Maintenance Engineer",
            "Sales Executive",
            "Procurement Manager",
            "Operations Manager",
            "Admin Officer",
            "Finance Manager",
            "Chief Executive Officer"
        ]

        designation_created = 0
        for title in designation_list:
            _, created = Designation.objects.get_or_create(designation=title)
            if created:
                designation_created += 1

        # ================= SUMMARY =================
        self.stdout.write(self.style.SUCCESS(f"""
            ====================================================
            Inventory Master Data Status
            ====================================================

            Procurement Types  : {msg(ProcurementType, procurement_created)}
            Departments        : {msg(Department, department_created)}
            Source Types       : {msg(SourceOfMake, source_created)}
            Tender Types       : {msg(TenderType, tender_created)}
            Units              : {msg(Units, units_created)}
            Delivery Types     : {msg(Delivery, delivery_created)}
            Stages             : {msg(Stages, stages_created)}
            Roles              : {msg(Roles, roles_created)}
            Designations       : {msg(Designation, designation_created)}

            ====================================================
        """))
