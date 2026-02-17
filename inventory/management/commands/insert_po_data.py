from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from catalog.models import Manufacturer, Product, Languages, Brand, ProductType, Category, ProductLinks, ProductAttribute, Attribute
from location.models import Country, Location, SubLocation
from application.models import AppSettings, Themes
from vendor.models import Vendor, VendorType, VendorAttachment, VendorTax, VendorBank,ProductVendor,VendorUpload
from catalog.models import ProductUpload,ProductGroup
from customer.models import Customer
from accounts.models import User
from project.models import ProjectHeader, ProjectComponent, BOMHeader, BOMItem,BOMAttachments, VoucherHeader
from inventory.models import PurchaseOrderType, PurchaseOrderStatus, PurchaseOrderHeader, PurchaseOrderItem, GoodsMovementHeader, GoodsMovementItem, PurchaseOrderHistory, Inventory


class Command(BaseCommand):
    help = "Setup standardized role-based permissions for all models."

    ROLE_PERMISSIONS = {
        "Administrator": ["can_create", "can_edit", "can_delete", "can_view"],
        "staff": ["can_create", "can_view"],
        "Guest": ["can_view"],
    }

    MODEL_CLASSES = [
        Manufacturer, Languages, Brand, ProductType, Category,
        Country, ProductLinks, ProductAttribute, Attribute, Location,SubLocation,
        AppSettings, Themes,  Product,
        Vendor, VendorType, VendorAttachment, VendorTax, VendorBank,ProductVendor,VendorUpload,ProductUpload,ProductGroup,
        PurchaseOrderType, PurchaseOrderStatus, PurchaseOrderHeader, PurchaseOrderItem, GoodsMovementHeader, 
        GoodsMovementItem, PurchaseOrderHistory, Inventory, Customer, ProjectHeader, ProjectComponent, 
        BOMHeader, BOMItem ,BOMAttachments, VoucherHeader
    ]

    def handle(self, *args, **kwargs):
        self.create_groups()
        self.assign_permissions()
        self.stdout.write(self.style.SUCCESS("Role-based permissions setup complete!"))

    def create_groups(self):
        """Ensure all groups exist."""
        for role in self.ROLE_PERMISSIONS:
            group, created = Group.objects.get_or_create(name=role)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created group: {role}"))
            else:
                self.stdout.write(f"Group already exists: {role}")

    def assign_permissions(self):
        """Assign model permissions to each group."""
        Group.permissions.through.objects.all().delete()
        for model in self.MODEL_CLASSES:
            content_type = ContentType.objects.get_for_model(model)
            model_name = model._meta.model_name

            for role, actions in self.ROLE_PERMISSIONS.items():
                group = Group.objects.get(name=role)

                for action in actions:
                    codename = f"{action}_{model_name}"
                    permission = Permission.objects.filter(
                        codename=codename, content_type=content_type
                    ).first()

                    if permission:
                        group.permissions.add(permission)
                        self.stdout.write(self.style.SUCCESS(f"Assigned {codename} → {role}"))
                    else:
                        self.stdout.write(self.style.WARNING(
                            f"Missing permission: {codename} for model {model.__name__}"
                        ))
