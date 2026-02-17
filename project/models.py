import re
import math

from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils.text import slugify

from auditlog.registry import auditlog

from core.models import TimeStampBaseModel, UserLogBaseModel, PurchaseOrderBaseModel
from location.models import Country, Location, SubLocation
from customer.models import Customer
from catalog.models import Product
from inventory.models import PurchaseOrderStatus, UOM_CHOICES, Inventory




COMPONENT_TYPES = [
    ("BOM", "Bom"),
    ("PRODUCT", "Product"),
    ("SERVICE", "Service"),
    ("MISCELLANEOUS","Miscellaneous")
]

ITEM_STATUS_CHOICES = [
    ("OPEN", "Open"),
    ("CLOSED", "Closed"),
    ("PARTIAL", "Partial")
]

VOUCHER_ITEM_STATUS_CHOICES = [
    ("OPEN", "Open"),
    ('IN_BUILD', 'IN_BUILD'),
    ('COMPLETED','COMPLETED'),
    ('CANCELLED','CANCELLED')
]

ATTACHMENT_TYPES = [
    ("URL", "URL"),
    ("FILE", "File"),
]


# ----------------------------
# ProjectHeader
# ----------------------------
class ProjectHeader(PurchaseOrderBaseModel, UserLogBaseModel, TimeStampBaseModel):
    project = models.ForeignKey(
        "ims.Project",
        on_delete=models.PROTECT,
        verbose_name="project ID",
        related_name="project_ID"
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        verbose_name="customer Name",
        related_name="customer_name"
    )
    location = models.ForeignKey(
        Location, on_delete=models.PROTECT, blank=True, null=True,
        related_name="Location", verbose_name="Location"
    )
    sub_location = models.ForeignKey(
        SubLocation, on_delete=models.PROTECT, blank=True, null=True,
        related_name="Sub_Location", verbose_name="SubLocation"
    )
    item_status = models.CharField(
        max_length=20, choices=ITEM_STATUS_CHOICES,
        verbose_name="Item Status"
    )
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Project Header"
        verbose_name_plural = "Project Header List"
        permissions = [
            ("can_create_projectheader", "Can create project header"),
            ("can_edit_projectheader", "Can edit project header"),
            ("can_view_projectheader", "Can view project header"),
            ("can_delete_projectheader", "Can delete project header"),
        ]

    def __str__(self):
        return f"{self.project.project_id} - {self.project.name}"

    @property
    def get_name(self):
        return self.project.name

    @property
    def total_component_cost(self):
        """Returns total cost of all project components"""
        return (
            self.project_ID
            .aggregate(
                total=Coalesce(Sum("component_cost"), Value(0))
            )["total"]
        )


    def save(self, *args, **kwargs):
        if self.project:
            self.project = self.project
        if not self.slug:
            self.slug = slugify(self.project)
        self.full_clean()
        super().save(*args, **kwargs)
    
    def getItems(self):
        return ProjectComponent.objects.filter(project_id=self.pk)


# ----------------------------
# BOMHeader
# ----------------------------
class BOMHeader(PurchaseOrderBaseModel, UserLogBaseModel, TimeStampBaseModel):
    code = models.CharField(
        max_length=30,
        verbose_name="BOM ID",
        help_text="BOM ID",
        unique=True,
        db_index=True
    )
    project = models.ForeignKey(
        ProjectHeader,
        on_delete=models.PROTECT,
        verbose_name="Project Header ID",
        related_name="project_header_id"
    )
    #quantity = models.PositiveIntegerField(verbose_name="BOM Qty", default=1,help_text="Finished goods quantity this BOM produces") 
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "BOM Header"
        verbose_name_plural = "BOM Header List"
        permissions = [
            ("can_create_bomheader", "Can create bom header"),
            ("can_edit_bomheader", "Can edit bom header"),
            ("can_view_bomheader", "Can view bom header"),
            ("can_delete_bomheader", "Can delete bom header"),
        ]

    def __str__(self):
        return f"{self.code}"


    def clean(self):
        # Ensure slug is unique BEFORE saving
        slug = slugify(self.code)
        if BOMHeader.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            raise ValidationError({"code": "BOMHeader with this BOM ID already exists."})

        # Ensure code is unique and normalized
        if self.code:
            normalized_code = self.code.strip().upper()
            if BOMHeader.objects.exclude(pk=self.pk).filter(code=normalized_code).exists():
                raise ValidationError({"code": "BOM ID already exists."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.code)
        if self.code:
            self.code = self.code.strip().upper()
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def get_name(self):
        return self.project.project.name
   
    def getItems(self):
        
        bom_items = (
            BOMItem.objects
            .filter(bom_id=self.pk)
            .select_related("product")
            .annotate(
                inventory_qty=Coalesce(
                    Sum("product__inventory_items__quantity"),
                    Value(0),
                    output_field=models.DecimalField(max_digits=15, decimal_places=2)
                )
            )
        )

        for item in bom_items:
            item.issued_qty = 0
            item.balance_qty = item.bom_quantity
            item.has_stock = item.inventory_qty >= item.bom_quantity

        return bom_items
    
# ----------------------------
# ProjectComponent
# ----------------------------
class ProjectComponent(PurchaseOrderBaseModel, UserLogBaseModel, TimeStampBaseModel):
    project = models.ForeignKey(
        ProjectHeader,
        on_delete=models.PROTECT,
        verbose_name="project ID",
        related_name="project_ID"
    )
    code = models.CharField(
        max_length=100,
        verbose_name="Project Component Document",
        help_text="Project Component Document",
        unique=True,
        db_index=True
    )
    component_type = models.CharField(
        max_length=20, choices=COMPONENT_TYPES, verbose_name="Component Type"
    )
    bom = models.ForeignKey(
        BOMHeader,
        on_delete=models.PROTECT,
        blank=True, null=True,
        verbose_name="BOM Header ID",
        related_name="BOM_HEADER_ID"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        blank=True, null=True,
        verbose_name="Product ID",
        related_name="Product"
    )
    service = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        blank=True, null=True,
        verbose_name="Service ID",
        related_name="Service"
    )
    miscellaneous_component = models.TextField(
        verbose_name="Miscellaneous Component Text", blank=True, null=True
    )
    component_qty = models.PositiveIntegerField(verbose_name="Component Qty", default=0)
    component_cost = models.PositiveIntegerField(verbose_name="Component Cost", default=0)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Project Component"
        verbose_name_plural = "Project Component List"
        permissions = [
            ("can_create_projectcomponent", "Can create project Component"),
            ("can_edit_projectcomponent", "Can edit project Component"),
            ("can_view_projectcomponent", "Can view project Component"),
            ("can_delete_projectcomponent", "Can delete project Component"),
        ]

    def __str__(self):
        return f"{self.code}"

    @property
    def get_name(self):
        return self.code
    # @property
    # def issued_qty(self):
    #     return (
    #         self.issued_components
    #         .aggregate(total=Sum("voucher_qty"))["total"] or 0
    #     )
    # def get_bom_item_issued_qty(self, bom_item):
    #     return (
    #         self.issued_components
    #         .filter(inventory__product=bom_item.product)
    #         .aggregate(total=Sum("voucher_qty"))["total"] or 0
    #     )

    # def get_issued_bom_units(self,bom_item):
    #     if self.component_type != "BOM" or not self.bom:
    #         return 0

    #     issued_units = []

    #     for item in self.bom.BOM_ID.filter(pk=bom_item.pk):
    #         bom_qty = item.bom_quantity*self.component_qty
            

    #     return bom_qty

    # def get_bom_item_balance_qty(self, bom_item):
    #     issue_qty = self.get_bom_item_issued_qty(bom_item)
    #     bom_qty = self.get_issued_bom_units(bom_item)
    #     balance_bom_units =bom_qty - issue_qty
    #     return balance_bom_units
    # @property
    # def balance_bom_qty(self):
    #     """
    #     Returns maximum BOM qty that can be issued
    #     based on current inventory.
    #     """

    #     if self.component_type != "BOM" or not self.bom:
    #         return None

    #     project = self.project
    #     balance_qty = None

    #     for item in self.bom.BOM_ID.all():
    #         print("item",item)
    #         inv = Inventory.objects.filter(
    #             product=item.product,
    #             location=project.location,
    #             sub_location=project.sub_location
    #         ).first()

    #         # ❌ If any item has no stock → BOM not possible
    #         if not inv or inv.quantity <= 0:
    #             return 0

    #         possible = inv.quantity // item.quantity

    #         balance_qty = (
    #             possible if balance_qty is None
    #             else min(balance_qty, possible)
    #         )

    #     return balance_qty or 0
    @property
    def issued_qty(self):
        return (
            self.issued_components
            .aggregate(total=Sum("voucher_qty"))
            .get("total") or 0
        )

    # ----------------------------------------------------
    # ISSUED QTY FOR A SPECIFIC BOM ITEM
    # ----------------------------------------------------
    def get_bom_item_issued_qty(self, bom_item):
        return (
            self.issued_components
            .filter(inventory__product=bom_item.product)
            .aggregate(total=Sum("voucher_qty"))
            .get("total") or 0
        )

    # ----------------------------------------------------
    # TOTAL REQUIRED QTY FOR A BOM ITEM
    # ----------------------------------------------------
    def get_bom_item_required_qty(self, bom_item):
        """
        Total required qty for this BOM item
        based on component qty
        """

        if self.component_type != "BOM" or not self.bom:
            return 0

        bom_output_qty = self.component_qty or 1

        return self.component_qty * bom_item.bom_quantity
    # ----------------------------------------------------
    # BALANCE QTY FOR A BOM ITEM
    # ----------------------------------------------------
    def get_bom_item_balance_qty(self, bom_item):
        required_qty = self.get_bom_item_required_qty(bom_item)
        issued_qty = self.get_bom_item_issued_qty(bom_item)

        balance_qty = required_qty - issued_qty
        return balance_qty
    @property
    def get_issued_bom_qty(self):
        """Returns how many BOM units are already issued
        (minimum possible based on issued item quantities)
            """

        if self.component_type != "BOM" or not self.bom:
            return 0

        issued_units = None
        bom_output_qty = self.component_qty or 1

        for item in self.bom.BOM_ID.all()[:1]:
            issued_item_qty = (
                self.issued_components
                .filter(inventory__product=item.product,inventory__location=item.bom.project.location,
                inventory__sub_location=item.bom.project.sub_location)
                .aggregate(total=Sum("voucher_qty"))
                .get("total") or 0
            )
            issued_units = issued_item_qty//item.bom_quantity
            print(issued_units,"hhhhhhhhhhhhhhhhh")
            
        
        return issued_units or 0

    # ----------------------------------------------------
    # MAX BOM UNITS POSSIBLE (COMPONENT LEVEL)
    # ----------------------------------------------------
    @property
    def balance_bom_qty(self):
        """
        Maximum BOM units possible
        """

        if self.component_type != "BOM" or not self.bom:
            return 0

        balance = None
        bom_output_qty = self.component_qty or 1
        balance = bom_output_qty-self.get_issued_bom_qty

        # for item in self.bom.BOM_ID.all():

        #     inv = Inventory.objects.filter(
        #         product=item.product,
        #         location=self.project.location,
        #         sub_location=self.project.sub_location
        #     ).first()

        #     if not inv or inv.quantity <= 0:
        #         return 0

        #     possible = (
        #         inv.quantity * bom_output_qty
        #     ) // item.bom_quantity

        #     balance = possible if balance is None else min(balance, possible)

        return balance or 0

    # ----------------------------------------------------
    # QUICK CHECK
    # ----------------------------------------------------
    @property
    def has_bom_stock(self):
        return self.balance_bom_qty > 0
    @property
    def balance_qty(self):
        # if self.component_type=="BOM":
        #    bom_item = BOMItem.objects.get(pk=self.)
        #    return self.bom.BOM_ID.all()[0].bom_quantity - self.issued_qty

        return self.component_qty - self.issued_qty
    
    @property
    def issue_status(self):
        if self.issued_qty == 0:
            return "OPEN"
        elif self.issued_qty < self.component_qty:
            return "PARTIAL"
        return "CLOSED"
    @property
    def getVCHistory(self):
        return self.issued_components.all()
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if is_new and not self.code:
            project_code = self.project.project.project_id  # correct field

            # Atomic transaction to avoid race conditions
            with transaction.atomic():
                # Lock existing components of this project
                last_component = (
                    ProjectComponent.objects
                    .select_for_update()
                    .filter(project=self.project, code__startswith=f"{project_code}-")
                    .order_by("-created_at")
                    .first()
                )

                if last_component:
                    match = re.search(r"-(\d+)$", last_component.code)
                    last_number = int(match.group(1)) if match else 0
                else:
                    last_number = 0

                next_number = last_number + 1
                # Format with hyphen and 3 digits: INV-001
                self.code = f"{project_code}-{next_number:03d}"

        # Generate slug
        if not self.slug and self.code:
            self.slug = slugify(self.code)

        # Save once
        super().save(*args, **kwargs)

# ----------------------------
# BOM Item
# ----------------------------
class BOMItem(PurchaseOrderBaseModel, UserLogBaseModel, TimeStampBaseModel):
    bom = models.ForeignKey(
        BOMHeader,
        on_delete=models.PROTECT,
        blank=True, null=True,
        verbose_name="BOM ID",
        related_name="BOM_ID"
    )
    code = models.CharField(
        max_length=100,
        verbose_name="BOM Component ID",
        help_text="BOM Component ID",
        unique=True,
        db_index=True,
        blank=True,
        null=True
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        blank=True, null=True,
        verbose_name="Product ID",
        related_name="Product_ID"
    )
    bom_quantity = models.PositiveIntegerField(verbose_name="Component Quantity", default=0)
    bom_uom = models.CharField(
        max_length=10, choices=UOM_CHOICES,
        verbose_name="Component UOM"
    )
    scrap_percentage = models.PositiveIntegerField(verbose_name="Scrap Percentage", default=0)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "BOM Item"
        verbose_name_plural = "BOM Item List"
        permissions = [
            ("can_create_bomitem", "Can create BOM Item"),
            ("can_edit_bomitem", "Can edit BOM Item"),
            ("can_view_bomitem", "Can view BOM Item"),
            ("can_delete_bomitem", "Can delete BOM Item"),
        ]

    def __str__(self):
        return f"{self.code}"

    @property
    def get_name(self):
        return self.code
    # @property
    # def issued_qty(self):
    #     pc= ProjectComponent.objects.get(bom=self.bom)
    #     return (
    #         pc.issued_components.filter(inventory__product=self.product)
    #         .aggregate(total=Sum("voucher_qty"))["total"] or 0
    #     )

    # @property
    # def balance_qty(self):
    #     print(self.bom_quantity,self.issued_qty,"self.issued_qtyself.issued_qty")
    #     return self.bom_quantity - self.issued_qty
    @property
    def getInventory(self):
        
        inventory_qty = (
                self.product.inventory_items.filter(location=self.bom.project.location,
                        sub_location=self.bom.project.sub_location)
                .aggregate(
                    qty=Coalesce(
                        Sum("quantity"),
                        Value(0),
                        output_field=models.DecimalField(
                            max_digits=15,
                            decimal_places=2
                        )
                    )
                )["qty"]
            )
        print("getInventorygetInventory",inventory_qty)
        return inventory_qty

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if is_new and not self.code and self.bom:
            # Get BOM code
            bom_code = self.bom.code  # e.g., "BOM-CITYMALL"

            # Atomic transaction to avoid duplicates
            with transaction.atomic():
                # Lock existing BOM items of this BOM
                last_item = (
                    BOMItem.objects
                    .select_for_update()
                    .filter(bom=self.bom, code__startswith=f"{bom_code}-")
                    .order_by("-created_at")
                    .first()
                )

                if last_item:
                    match = re.search(r"-(\d+)$", last_item.code)
                    last_number = int(match.group(1)) if match else 0
                else:
                    last_number = 0

                next_number = last_number + 1
                # Format: BOM-CITYMALL-001
                self.code = f"{bom_code}-{next_number:03d}"

        # Generate slug from code
        if not self.slug and self.code:
            self.slug = slugify(self.code)

        super().save(*args, **kwargs)

# ----------------------------
# Attachment Types
# ----------------------------
class AttachmentType(models.TextChoices):
    URL = "URL", "URL"
    FILE = "FILE", "File"


class BOMAttachments(PurchaseOrderBaseModel, UserLogBaseModel, TimeStampBaseModel):
    class AttachmentType(models.TextChoices):
        FILE = 'FILE', 'File'
        URL = 'URL', 'URL'

    bom = models.ForeignKey(
        BOMHeader,
        on_delete=models.PROTECT,
        verbose_name="BOM",
        related_name="attachments"
    )
    attachment_type = models.CharField(
        max_length=4,
        choices=AttachmentType.choices,
        verbose_name="Attachment Type"
    )
    title = models.CharField(max_length=255, verbose_name="Attachment Title")
    url = models.TextField(blank=True, null=True, verbose_name="External URL")
    
    # File upload field
    file_upload = models.FileField(
        blank=True,
        null=True,
        upload_to='bom_attachments/',
        verbose_name="Upload File"
    )
    file_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="File Name")
    mime_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="MIME Type")
    file_size = models.BigIntegerField(blank=True, null=True, verbose_name="File Size (bytes)")

    class Meta:
        db_table = "bom_attachments"
        ordering = ["id"]  # Use PK ordering
        verbose_name = "BOM Attachment"
        verbose_name_plural = "BOM Attachments"
        permissions = [
            ("can_create_bomattachments", "Can create BOM Attachments"),
            ("can_edit_bomattachments", "Can edit BOM Attachments"),
            ("can_view_bomattachments", "Can view BOM Attachments"),
            ("can_delete_bomattachments", "Can delete BOM Attachments"),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(attachment_type='URL', url__isnull=False) |
                    Q(attachment_type='FILE', file_upload__isnull=False)
                ),
                name="chk_bom_attachment_url_or_file"
            )
        ]

    @property
    def get_name(self):
        return f"{self.bom} - {self.title}" 
    
    @property
    def status_name(self):
        return self.get_status_display() if self.status is not None else "-"

    # -----------------------------
    # Model-level validation
    # -----------------------------
    def clean(self):
        if self.attachment_type == self.AttachmentType.URL:
            if not self.url:
                raise ValidationError("URL is required for URL attachments.")
            # Clear file info if URL is used
            self.file_upload = None
            self.file_name = None
            self.mime_type = None
            self.file_size = None

        elif self.attachment_type == self.AttachmentType.FILE:
            if not self.file_upload:
                raise ValidationError("File upload is required for FILE attachments.")
            # Automatically fill file metadata
            self.file_name = self.file_upload.name
            self.file_size = self.file_upload.size
            self.mime_type = self.file_upload.file.content_type if hasattr(self.file_upload.file, 'content_type') else None
            # Clear URL if file is uploaded
            self.url = None

    # -----------------------------
    # Save
    # -----------------------------
    def save(self, *args, **kwargs):
        self.full_clean()  # Runs clean() before saving
        super().save(*args, **kwargs)


# # ----------------------------
# # VoucherHeader
# # ----------------------------
class VoucherHeader(PurchaseOrderBaseModel, UserLogBaseModel, TimeStampBaseModel):
    code = models.CharField(
        max_length=100,
        verbose_name="Voucher ID",
        help_text="Voucher ID",
        unique=True,
        #db_index=True,
    )
    project = models.ForeignKey(
        ProjectHeader,
        on_delete=models.PROTECT,
        verbose_name="project ID",
        related_name="voucher_headers"
    )
    voucher_status = models.CharField(
        max_length=20, choices=VOUCHER_ITEM_STATUS_CHOICES,
        verbose_name="Voucher Status"
    )
    voucher_qty = models.PositiveIntegerField(verbose_name="Voucher Qty", default=0)
    #slug = models.SlugField(max_length=255, unique=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Voucher Header"
        verbose_name_plural = "Voucher Header List"
        permissions = [
            ("can_create_voucherheader", "Can create voucher header"),
            ("can_edit_voucherheader", "Can edit voucher header"),
            ("can_view_voucherheader", "Can view voucher header"),
            ("can_delete_voucherheader", "Can delete voucher header"),
        ]

    def __str__(self):
        return f"{self.project.project_id}"

    def getItems(self):
        return VoucherComponent.objects.filter(voucherheader_id=self.pk)



# ----------------------------
# VoucherComponent
# ----------------------------
class VoucherComponent(PurchaseOrderBaseModel, UserLogBaseModel, TimeStampBaseModel):
    code = models.CharField(
        max_length=100,
        verbose_name="Voucher Component ID",
        help_text="Voucher Component ID",
        unique=True,
        db_index=True,
    )
    voucherheader = models.ForeignKey(
        VoucherHeader,
        on_delete=models.PROTECT,
        verbose_name="Voucher Header",
        related_name="voucher_components"
    )
    projectcomponent = models.ForeignKey(
        ProjectComponent,
        on_delete=models.PROTECT,
        verbose_name="Project Component",
        related_name="issued_components"
    )
    inventory = models.ForeignKey(
        Inventory,
        on_delete=models.PROTECT,
        blank=True,null=True,
        verbose_name="Inventory",
        related_name="inventory_issues"
    )
    voucher_qty = models.PositiveIntegerField(verbose_name="Voucher Qty", default=0)
    #slug = models.SlugField(max_length=255, unique=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Voucher Component"
        verbose_name_plural = "Voucher Component List"
        permissions = [
            ("can_create_vouchercomponent", "Can create voucher component"),
            ("can_edit_vouchercomponent", "Can edit voucher component"),
            ("can_view_vouchercomponent", "Can view voucher component"),
            ("can_delete_vouchercomponent", "Can delete voucher component"),
        ]

    def __str__(self):
        return f"{self.code}"



auditlog.register(ProjectComponent)
auditlog.register(ProjectHeader)
auditlog.register(BOMHeader)
auditlog.register(BOMItem)
auditlog.register(BOMAttachments)
