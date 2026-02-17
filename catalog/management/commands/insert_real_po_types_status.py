import random
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from inventory.models import (
    PurchaseOrderType, PurchaseOrderStatus
)

STATUS_CHOICES = [
    (-1, "Inactive"),
    (0, "Draft"),
    (1, "Active"),
]

class Command(BaseCommand):
    help = "Insert 50 realistic PurchaseOrderType and PurchaseOrderStatus records with description, search keywords, and status"

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting insertion of realistic PurchaseOrderType and PurchaseOrderStatus...")

        status_choices = [choice[0] for choice in STATUS_CHOICES]

        # ------------------ Realistic PO Types ------------------
        po_type_names = [
            "Standard Purchase", "Urgent Purchase", "Contract Purchase", "Consignment Purchase",
            "Stock Replenishment", "Project Purchase", "Trial Purchase", "Bulk Purchase",
            "Capital Purchase", "Recurring Purchase", "One-time Purchase", "Local Purchase",
            "Import Purchase", "Export Purchase", "Special Order", "Service Purchase",
            "Maintenance Purchase", "Repair Purchase", "Subcontract Purchase", "Replacement Purchase",
            "Promotional Purchase", "Sample Purchase", "Test Purchase", "Emergency Purchase",
            "Framework Agreement Purchase", "Strategic Purchase", "Operational Purchase", "Seasonal Purchase",
            "Inventory Purchase", "Raw Material Purchase", "Finished Goods Purchase", "Work-in-Progress Purchase",
            "MRO Purchase", "IT Equipment Purchase", "Furniture Purchase", "Office Supplies Purchase",
            "Equipment Rental Purchase", "Consulting Services Purchase", "Software License Purchase",
            "Training Purchase", "Research Purchase", "Marketing Purchase", "Event Purchase",
            "Outsourcing Purchase", "Subcontracting Purchase", "Replacement Stock Purchase",
            "Quality Test Purchase", "Packaging Purchase", "Logistics Purchase", "Miscellaneous Purchase"
        ]

        po_types_inserted = 0
        for i, name in enumerate(po_type_names, start=1):
            code = f"PO_TYPE_{i:03}"
            description = f"This is a {name.lower()} order type used for various purchase processes."
            search_keywords = ", ".join([word.lower() for word in name.split()])
            status = random.choice(status_choices)

            try:
                po_type, created = PurchaseOrderType.objects.get_or_create(
                    code=code,
                    defaults={
                        "name": name,
                        "slug": slugify(name),
                        "description": description,
                        "search_keywords": search_keywords,
                        "status": status
                    }
                )
                if created:
                    po_types_inserted += 1
            except Exception as e:
                self.stdout.write(f"Error inserting PO Type {name}: {e}")

        self.stdout.write(self.style.SUCCESS(f"{po_types_inserted} PurchaseOrderType records inserted."))

        # ------------------ Realistic PO Status ------------------
        po_status_names = [
            "OPEN", "CLOSED", "PARTIALLY COMPLETED", "PENDING APPROVAL", "APPROVED",
            "REJECTED", "IN PROGRESS", "ON HOLD", "CANCELLED", "COMPLETED",
            "DRAFT", "CONFIRMED", "BACKORDERED", "SHIPPED", "DELIVERED",
            "RECEIVED", "RETURNED", "INVOICED", "PAID", "OVERDUE",
            "PENDING PAYMENT", "QUALITY CHECK", "BLOCKED", "RELEASED", "TRANSFERRED",
            "PENDING DISPATCH", "PARTIAL DELIVERY", "UNDER REVIEW", "IN ESCALATION", "AWAITING CONFIRMATION",
            "SCHEDULED", "DELAYED", "EXPEDITED", "REOPENED", "VERIFIED",
            "PENDING SUPPLIER", "PENDING CUSTOMER", "ON TRACK", "AT RISK", "FROZEN",
            "ALLOCATED", "UNALLOCATED", "PENDING STOCK", "PENDING SHIPMENT", "RETURNED TO SUPPLIER",
            "STOCK RECEIVED", "STOCK ISSUED", "PENDING INSPECTION", "INSPECTION COMPLETED", "FINALIZED"
        ]

        po_status_inserted = 0
        for i, name in enumerate(po_status_names, start=1):
            code = f"PO_STATUS_{i:03}"
            description = f"Status indicating that the purchase order is '{name.lower()}'."
            search_keywords = ", ".join([word.lower() for word in name.split()])
            status = random.choice(status_choices)

            try:
                po_status, created = PurchaseOrderStatus.objects.get_or_create(
                    code=code,
                    defaults={
                        "name": name,
                        "slug": slugify(name),
                        "description": description,
                        "search_keywords": search_keywords,
                        "status": status
                    }
                )
                if created:
                    po_status_inserted += 1
            except Exception as e:
                self.stdout.write(f"Error inserting PO Status {name}: {e}")

        self.stdout.write(self.style.SUCCESS(f"{po_status_inserted} PurchaseOrderStatus records inserted."))
