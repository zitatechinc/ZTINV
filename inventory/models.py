from django.db import models
from django.apps import apps
from core.models import TimeStampBaseModel, VendorBaseModel, UserLogBaseModel, PurchaseOrderBaseModel
from location.models import Country, Location, SubLocation
from accounts.models import User
from vendor.models import Vendor
from catalog.models import Product, Languages
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db.models import Sum


# Create your models here.
class PurchaseOrderType(PurchaseOrderBaseModel,UserLogBaseModel, TimeStampBaseModel):
    name = models.CharField(
        max_length=250,
        unique=True,
        verbose_name="Name",
        help_text="Purchase Order Type Name"
    )
    code = models.CharField(
        max_length=100,
        verbose_name="Code",
        help_text="Unique identifier code",
        unique=True
    )
    slug = models.SlugField(max_length=255, unique=True, blank=True)
   

    class Meta:
        ordering = ['name']
        verbose_name = "Purchase Order Type"
        verbose_name_plural = f"{verbose_name} List"
        permissions = [
            ("can_create_purchaseordertype", "Can Create PurchaseOrderType"),
            ("can_edit_purchaseordertype", "Can Edit PurchaseOrderType"),
            ("can_view_purchaseordertype", "Can View PurchaseOrderType"),
            ("can_delete_purchaseordertype", "Can Delete PurchaseOrderType"),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def clean(self):
        # Ensure slug is unique BEFORE saving
        slug = slugify(self.name)
        if PurchaseOrderType.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            raise ValidationError({"name": "PurchaseOrderType with this Name already exists."})

        if self.code:
            normalized_code = self.code.strip().upper()
            if PurchaseOrderType.objects.exclude(pk=self.pk).filter(code=normalized_code).exists():
                raise ValidationError({"code": "Code already exists."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.full_clean()

        if hasattr(self, "code") and self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

class PurchaseOrderStatus(PurchaseOrderBaseModel,UserLogBaseModel, TimeStampBaseModel):
    name = models.CharField(
        max_length=250,
        unique=True,
        verbose_name="Name",
        help_text="Purchase Order Status Name"
    )
    code = models.CharField(
        max_length=100,
        verbose_name="Code",
        help_text="Unique identifier code",
        unique=True
    )
    slug = models.SlugField(max_length=255, unique=True, blank=True)
   

    class Meta:
        ordering = ['name']
        verbose_name = "Purchase Order Status"
        verbose_name_plural = f"{verbose_name} List"
        permissions = [
            ("can_create_purchaseorderstatus", "Can Create PurchaseOrderStatus"),
            ("can_edit_purchaseorderstatus", "Can Edit PurchaseOrderStatus"),
            ("can_view_purchaseorderstatus", "Can View PurchaseOrderStatus"),
            ("can_delete_purchaseorderstatus", "Can Delete PurchaseOrderStatus"),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def clean(self):
        # Ensure slug is unique BEFORE saving
        slug = slugify(self.name)
        if PurchaseOrderStatus.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            raise ValidationError({"name": "PurchaseOrderStatus with this Name already exists."})

        if self.code:
            normalized_code = self.code.strip().upper()
            if PurchaseOrderStatus.objects.exclude(pk=self.pk).filter(code=normalized_code).exists():
                raise ValidationError({"code": "Code already exists."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.full_clean()

        if hasattr(self, "code") and self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)


UOM_CHOICES = [
    ("PCS", "Pieces"),
    ("KG", "Kilogram"),
    ("LTR", "Liter"),
    ("EA","Each"),
    ("DZ","Dozen"),
    ("BOX","Box"),
    ("SET","Set"),
    ('Nos', 'Nos')
]

# def UOM_CHOICES():
#     Units = apps.get_model('ims', 'Units')
#     return [(u.unit, u.unit) for u in Units.objects.all()]

ITEM_STATUS_CHOICES = [
    ("OPEN", "Open"),
    ("CLOSED", "Closed"),
    ("PARTIAL", "Partial"),
]

GM_CATEGORY_CHOICES = [
    ("Goods Receipt", "Goods Receipt"),
    ("Quality Management", "Quality Management"),
    ("Goods Issue", "Goods Issue"),
    ("Transfer Posting", "Transfer Posting"),
    ("Stock Transfer", "Stock Transfer"),
    ("Reversal / Cancellation", "Reversal / Cancellation"),
    ("Subcontracting / Special", "Subcontracting / Special"),
    ("Other", "Other"),
]

GM_TYPE_CHOICES = GM_CATEGORY_CHOICES + [("Receipt", "Receipt")]

PO_HISTORY_TYPE_CHOICES = [
    ("GR", "Goods Receipt"),
    ("RE", "Invoice Receipt"),
    ("WA", "Goods Issue"),
    ("WB", "GR - Blocked Stock"),
    ("WF", "GR - Free of Charge"),
    ("WG", "Delivery Costs"),
    ("WL", "Subcontracting GR/Delivery"),
    ("WR", "Invoice Reduction"),
    ("WS", "Subcontracting Charges"),
    ("ML", "Material Ledger Settlement"),
    ("QM", "Quality Management Posting"),
    ("MR", "Invoice Receipt Reversal"),
    ("ST", "Stock Transfer Posting"),
]

INVENTORY_TYPE_CHOICES = [
    ("RM", "Raw Materials"),
    ("WIP", "Work-in-Progress"),
    ("FG", "Finished Goods"),
    ("OH", "On-Hand Inventory"),
    ("MRO", "Maintenance, Repair & Operations"),
    ("IT", "In-Transit"),
    ("CONSIGN", "Consignment"),
    ("SS", "Safety Stock"),
    ("BS", "Buffer Stock"),
    ("OBS", "Obsolete/Dead Stock"),
]

# ----------------------------
# PurchaseOrderHeader
# ----------------------------
class PurchaseOrderHeader(PurchaseOrderBaseModel, UserLogBaseModel, TimeStampBaseModel):
    code = models.CharField(
        max_length=100,
        verbose_name="PO Number",
        help_text="PO Number",
        unique=True,
        db_index=True
    )
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.PROTECT,
        verbose_name="Vendor",
        related_name="purchase_orders"
    )
    po_date = models.DateField(
        verbose_name="PO Date",
        help_text="Purchase Order Date"
    )
    po_requested_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name="PO Requested By",
        related_name="requested_pos"
    )
    po_status = models.ForeignKey(
        PurchaseOrderStatus,
        on_delete=models.PROTECT,
        verbose_name="PO Status",
        related_name="purchase_orders"
    )
    qm_header_status = models.ForeignKey(
        PurchaseOrderStatus,
        on_delete=models.PROTECT,
        verbose_name="QM Header Status",
        related_name="qm_header_status_orders"
    )
    po_type = models.ForeignKey(
        PurchaseOrderType,
        on_delete=models.PROTECT,
        verbose_name="PO Type",
        related_name="purchase_orders"
    )
    requested_delivery_date = models.DateField(
        verbose_name="Requested Delivery Date",
        help_text="Requested Delivery Date"
    )
    header_notes = models.TextField(
        verbose_name="Header Notes",
        help_text="Header Notes",
        blank=True,
        null=True
    )
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Purchase Order"
        verbose_name_plural = "Purchase Order List"
        permissions = [
            ("can_create_purchaseorderheader", "Can create purchase order header"),
            ("can_edit_purchaseorderheader", "Can edit purchase order header"),
            ("can_view_purchaseorderheader", "Can view purchase order header"),
            ("can_delete_purchaseorderheader", "Can delete purchase order header"),
        ]

    def __str__(self):
        return f"{self.code}"

    def getItems(self):
        return PurchaseOrderItem.objects.filter(po_header_id=self.pk)

    def clean(self):
        if self.code:
            normalized_code = self.code.strip().upper()
            if PurchaseOrderHeader.objects.exclude(pk=self.pk).filter(code=normalized_code).exists():
                raise ValidationError({"code": "Code already exists."})

    def save(self, *args, **kwargs):
        if self.code:
            self.code = self.code.strip().upper()
        if not self.slug:
            self.slug = slugify(self.code)
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def get_name(self):
        return self.code

# ----------------------------
# PurchaseOrderItem
# ----------------------------
class PurchaseOrderItem(PurchaseOrderBaseModel, UserLogBaseModel, TimeStampBaseModel):
    code = models.CharField(
        max_length=100,
        verbose_name="PO Item Line Number",
        unique=True,
        db_index=True
    )
    line_number = models.PositiveIntegerField(verbose_name="PO Line Number")
    po_header = models.ForeignKey(
        PurchaseOrderHeader,
        on_delete=models.PROTECT,
        verbose_name="PO Header",
        related_name="items"
    )
    item = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        verbose_name="Material/Product Number",
        related_name="po_items"
    )
    quantity = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Quantity"
    )
    uom = models.CharField(
        max_length=10, choices=UOM_CHOICES,
        verbose_name="Units of Measure"
    )
    unit_price = models.DecimalField(
        max_digits=12, decimal_places=3,
        verbose_name="Unit Price"
    )
    total_price = models.DecimalField(
        max_digits=15, decimal_places=3,
        verbose_name="Total Price",
        blank=True
    )
    already_received_qty = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Already Received Qty"
    )
    qty_being_received = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Qty Being Received"
    )
    yet_to_be_received_qty = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Yet to be Received"
    )
    item_status = models.CharField(
        max_length=50, choices=ITEM_STATUS_CHOICES,
        verbose_name="Item Status"
    )
    qty_inspection_status = models.CharField(
        max_length=50, choices=ITEM_STATUS_CHOICES, default="OPEN", verbose_name="qty Inspection Status"
    )
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    notes = models.TextField(
        verbose_name="Item Notes",
        blank=True, null=True
    )
    po_location = models.ForeignKey(
        Location, on_delete=models.PROTECT, blank=True, null=True,
        related_name="po_items", verbose_name="Location"
    )
    sub_location = models.ForeignKey(
        SubLocation, on_delete=models.PROTECT, blank=True, null=True,
        related_name="po_items", verbose_name="Sub Location"
    )

    qm_notes = models.TextField(verbose_name="QM Item Notes",blank=True, null=True)
    good_qty = models.PositiveIntegerField(verbose_name="Good Qty", default=0)
    rejected_qty = models.PositiveIntegerField(verbose_name="Rejected Qty", default=0)
    total_qty_inspected = models.PositiveIntegerField(verbose_name="Total qty Inspected", default=0)
    quality_already_inspected = models.PositiveIntegerField(verbose_name="Quality Already Inspected", default=0)
    quality_already_rejected = models.PositiveIntegerField(verbose_name="Quality Already Rejected", default=0)
    
    class Meta:
        unique_together = ("line_number", "item", "po_header")
        ordering = ['-created_at']
        verbose_name = "Purchase Order Item"
        verbose_name_plural = "Purchase Order Item List"
        permissions = [
            ("can_create_purchaseorderitem", "Can create purchase order item"),
            ("can_edit_purchaseorderitem", "Can edit purchase order item"),
            ("can_view_purchaseorderitem", "Can view purchase order item"),
            ("can_delete_purchaseorderitem", "Can delete purchase order item"),
        ]

    def __str__(self):
        return f"{self.code}"

    def save(self, *args, **kwargs):
        # if self.quantity and self.unit_price:
        #     self.total_price = float(self.quantity) * float(self.unit_price)
        if self.code:
            self.code = self.code.strip().upper()
        if not self.slug:
            self.slug = slugify(self.code)
        self.full_clean()
        super().save(*args, **kwargs)

    def getPOHistory(self):
        return PurchaseOrderHistory.objects.filter(po_header=self.po_header, po_line_number=self.line_number, product_id=self.pk).order_by('-id')
    
    def getSerialNumbers(self):
        return SerialNumber.objects.filter(po_header=self.po_header, po_item_id=self.pk).order_by('-id')
    @property
    def get_name(self):
        return self.code
    @property
    def yet_to_be_received(self):
        return self.quantity - self.already_received_qty

# ----------------------------
# GoodsMovementHeader
# ----------------------------
class GoodsMovementHeader(PurchaseOrderBaseModel, UserLogBaseModel, TimeStampBaseModel):
    code = models.CharField(
        max_length=100,
        verbose_name="GM Document",
        help_text="GM Document",
        unique=True,
        db_index=True
    )
    category = models.CharField(
        max_length=60,
        verbose_name="GM Category",
        choices=GM_CATEGORY_CHOICES
    )
    gm_date = models.DateField(
        verbose_name="GM Date",
        help_text="Goods Movement Date"
    )
    gm_posting_date = models.DateField(
        verbose_name="GM Posting Date",
        help_text="Goods Movement Posting Date"
    )
    po_header = models.ForeignKey(
        PurchaseOrderHeader,
        on_delete=models.PROTECT,
        verbose_name="PO Reference",
        related_name="goods_movements"
    )
    po_item = models.ForeignKey(
        PurchaseOrderItem, on_delete=models.PROTECT,
        related_name="gm_items", verbose_name="PO Item"
    )

    description = models.TextField(
        verbose_name="GM Text",
        blank=True, null=True
    )
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Goods Movement Header"
        verbose_name_plural = "Goods Movement Header List"
        permissions = [
            ("can_create_goodsmovementheader", "Can create goods movement header"),
            ("can_edit_goodsmovementheader", "Can edit goods movement header"),
            ("can_view_goodsmovementheader", "Can view goods movement header"),
            ("can_delete_goodsmovementheader", "Can delete goods movement header"),
        ]

    def __str__(self):
        return f"{self.code}"

    @property
    def get_name(self):
        return self.code

    def save(self, *args, **kwargs):
        if self.code:
            self.code = self.code
        if not self.slug:
            self.slug = slugify(self.code)
        self.full_clean()
        super().save(*args, **kwargs)


# ----------------------------
# GoodsMovementItem
# ----------------------------
class GoodsMovementItem(PurchaseOrderBaseModel, UserLogBaseModel, TimeStampBaseModel):
    code = models.CharField(
        max_length=100,
        verbose_name="GM Item Number",
        unique=True,
        db_index=True
    )
    document_number = models.ForeignKey(
        GoodsMovementHeader,
        on_delete=models.PROTECT,
        verbose_name="GM Document",
        related_name="items"
    )
    item_number = models.PositiveIntegerField(verbose_name="GM Item Number")
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        verbose_name="Material",
        related_name="gm_items"
    )
    location = models.ForeignKey(
        Location, on_delete=models.PROTECT, blank=True, null=True,
        related_name="gm_items", verbose_name="GM Location"
    )
    sub_location = models.ForeignKey(
        SubLocation, on_delete=models.PROTECT, blank=True, null=True,
        related_name="gm_items", verbose_name="GM Sub Location"
    )
    quantity = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        verbose_name="GM Quantity"
    )
    uom = models.CharField(
        max_length=10, choices=UOM_CHOICES, verbose_name="Units of Measure"
    )
    
    gm_type = models.CharField(
        max_length=60, choices=GM_TYPE_CHOICES, verbose_name="GM Type"
    )
    gm_item_text = models.TextField(
        verbose_name="GM Item Text", blank=True, null=True
    )
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Goods Movement Item"
        verbose_name_plural = "Goods Movement Item List"
        permissions = [
            ("can_create_goodsmovementitem", "Can create goods movement item"),
            ("can_edit_goodsmovementitem", "Can edit goods movement item"),
            ("can_view_goodsmovementitem", "Can view goods movement item"),
            ("can_delete_goodsmovementitem", "Can delete goods movement item"),
        ]

    def __str__(self):
        return f"{self.code}"

    @property
    def get_name(self):
        return self.code

    def save(self, *args, **kwargs):
        if self.code:
            #print(self.code,"ffffffffffff")
            self.code = self.code.strip().upper()
        if not self.slug:
            self.slug = slugify(self.code)
        self.full_clean()
        super().save(*args, **kwargs)


# ----------------------------
# PurchaseOrderHistory
# ----------------------------
class PurchaseOrderHistory(PurchaseOrderBaseModel, UserLogBaseModel, TimeStampBaseModel):
    po_header = models.ForeignKey(
        PurchaseOrderHeader,
        on_delete=models.PROTECT,
        verbose_name="PO Header",
        related_name="history"
    )
    po_line_number = models.PositiveIntegerField(verbose_name="PO Line Number")
    product = models.ForeignKey(
        PurchaseOrderItem,
        on_delete=models.PROTECT,
        verbose_name="Product",
        related_name="history"
    )
    po_history_number = models.PositiveIntegerField(verbose_name="PO History Number")
    po_history_type = models.CharField(
        max_length=60,
        choices=PO_HISTORY_TYPE_CHOICES,
        default="GR",
        verbose_name="PO History Type"
    )
    description = models.TextField(
        max_length=500, blank=True, null=True, verbose_name="Description"
    )
    gm_header = models.ForeignKey(
        GoodsMovementHeader,
        on_delete=models.PROTECT,
        verbose_name="GM Header",
        related_name="po_history"
    )
    po_history_date = models.DateField(
        verbose_name="PO History Date", help_text="PO History Date"
    )
    po_quantity = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="PO Quantity"
    )
    po_line_amount = models.DecimalField(
        max_digits=15, decimal_places=3, verbose_name="PO Line Amount"
    )
    uom = models.CharField(
        max_length=10, choices=UOM_CHOICES, verbose_name="Units of Measure"
    )

    po_good_qty = models.PositiveIntegerField(verbose_name="PO Good Qty", default=0)
    po_rejected_qty = models.PositiveIntegerField(verbose_name="PO Rejected Qty", default=0)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Purchase Order History"
        verbose_name_plural = "Purchase Order History"
        permissions = [
            ("can_create_purchaseorderhistory", "Can create purchase order history"),
            ("can_edit_purchaseorderhistory", "Can edit purchase order history"),
            ("can_view_purchaseorderhistory", "Can view purchase order history"),
            ("can_delete_purchaseorderhistory", "Can delete purchase order history"),
        ]

    def __str__(self):
        return f"{self.po_header.code}"

    @property
    def get_name(self):
        return self.po_header.code


# ----------------------------
# Inventory
# ----------------------------
class Inventory(PurchaseOrderBaseModel, TimeStampBaseModel, UserLogBaseModel):
    # code = models.CharField(
    #     max_length=100,
    #     verbose_name="Inventory Code",
    #     help_text="Inventory Code",
    #     unique=True,
    #     db_index=True
    # )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        verbose_name="Material",
        related_name="inventory_items"
    )
    uom = models.CharField(
        max_length=10, choices=UOM_CHOICES, verbose_name="Units of Measure"
    )
    inventory_type = models.CharField(
        max_length=100,
        choices=INVENTORY_TYPE_CHOICES,
        verbose_name="Inventory Type",
        help_text="Inventory Type"
    )
    location = models.ForeignKey(
        Location, on_delete=models.PROTECT, blank=True, null=True,
        related_name="inventory_items", verbose_name="Location"
    )
    sub_location = models.ForeignKey(
        SubLocation, on_delete=models.PROTECT, blank=True, null=True,
        related_name="inventory_items", verbose_name="Sub Location"
    )
    quantity = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Quantity"
    )

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Inventory"
        verbose_name_plural = "Inventory List"
        permissions = [
            ("can_create_inventory", "Can create inventory"),
            ("can_edit_inventory", "Can edit inventory"),
            ("can_view_inventory", "Can view inventory"),
            ("can_delete_inventory", "Can delete inventory"),
        ]

    def __str__(self):
        return f"{self.product.code}"

    @property
    def issued_qty(self):
        return (
            self.inventory_issues.aggregate(
                total=Sum("voucher_qty")
            )["total"] or 0
        )

    #@property
    # def get_name(self):
    #     return self.code



class SerialNumber(PurchaseOrderBaseModel, UserLogBaseModel, TimeStampBaseModel):
    """
    Stores unique serial numbers for serialized materials received via PO / Goods Movement.
    """

    serial_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Serial Number",
        help_text="Unique Serial Number for the material unit"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        verbose_name="Material Number",
        related_name="serial_numbers"
    )
    po_header = models.ForeignKey(
        PurchaseOrderHeader,
        on_delete=models.PROTECT,
        verbose_name="PO Header",
        related_name="serial_numbers"
    )
    po_item = models.ForeignKey(
        PurchaseOrderItem,
        on_delete=models.PROTECT,
        verbose_name="PO Item",
        related_name="serial_numbers"
    )
    gm_header = models.ForeignKey(
        GoodsMovementHeader,
        on_delete=models.PROTECT,
        verbose_name="Goods Movement Header",
        related_name="serial_numbers",
        null=True,
        blank=True
    )
    gm_item = models.ForeignKey(
        GoodsMovementItem,
        on_delete=models.PROTECT,
        verbose_name="Goods Movement Item",
        related_name="serial_numbers",
        null=True,
        blank=True
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="serial_numbers",
        verbose_name="Location"
    )
    sub_location = models.ForeignKey(
        SubLocation,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="serial_numbers",
        verbose_name="Sub Location"
    )

    remarks = models.TextField(
        verbose_name="Remarks / Notes",
        blank=True,
        null=True
    )
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Serial Number"
        verbose_name_plural = "Serial Number List"
        permissions = [
            ("can_create_serialnumber", "Can create serial number"),
            ("can_edit_serialnumber", "Can edit serial number"),
            ("can_view_serialnumber", "Can view serial number"),
            ("can_delete_serialnumber", "Can delete serial number"),
        ]

    def __str__(self):
        return f"{self.serial_number} - {self.product.code}"

    @property
    def get_name(self):
        return self.serial_number

    def clean(self):
        if self.serial_number:
            normalized_serial = self.serial_number.strip().upper()
            if SerialNumber.objects.exclude(pk=self.pk).filter(serial_number=normalized_serial).exists():
                raise ValidationError({"serial_number": "Serial Number already exists."})

    def save(self, *args, **kwargs):
        if self.serial_number:
            self.serial_number = self.serial_number.strip().upper()
        if not self.slug:
            self.slug = slugify(self.serial_number)
        self.full_clean()
        super().save(*args, **kwargs)
