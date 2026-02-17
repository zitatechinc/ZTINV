from django.db import models
from core.models import TimeStampBaseModel, VendorBaseModel, CatalogBaseModel, UserLogBaseModel, PurchaseOrderBaseModel
from location.models import Country, Location, SubLocation
from accounts.models import User
from catalog.models import Product, Languages
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from core.models import VENDOR_TYPE_CHOICES, STATUS_CHOICES, PAYMENT_TERM_CHOICES
from auditlog.registry import auditlog


class VendorType(CatalogBaseModel, VendorBaseModel, UserLogBaseModel, TimeStampBaseModel):
    
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Vendor Type"
        verbose_name_plural = f"{verbose_name} List"
        permissions = [
            ("can_create_vendortype", "Can Create vendor_type"),
            ("can_edit_vendortype", "Can Edit vendor_type"),
            ("can_view_vendortype", "Can View vendor_type"),
            ("can_delete_vendortype", "Can Delete vendor_type"),
        ]


    def __str__(self):
        return f"{self.name} ({self.code})"

    def clean(self):
        # Ensure slug is unique BEFORE saving
        slug = slugify(self.name)
        if VendorType.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            raise ValidationError({"name": "VendorType with this Name already exists."})

        if self.code:
            normalized_code = self.code.strip().upper()
            if VendorType.objects.exclude(pk=self.pk).filter(code=normalized_code).exists():
                raise ValidationError({"code": "Code already exists."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.full_clean()

        if hasattr(self, "code") and self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

        
class Vendor(VendorBaseModel, TimeStampBaseModel, UserLogBaseModel):
    code = models.CharField(
        max_length=100,
        verbose_name="Code",
        help_text="Unique identifier code",
        unique=True
    )
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    vendor_type = models.ForeignKey(VendorType, on_delete=models.PROTECT,  null=True, verbose_name='Vendor Type')
    company_name1 = models.CharField(max_length=250, verbose_name='Company Name1', unique=True)
    company_name2 = models.CharField(max_length=250, verbose_name='Company Name2',blank=True,null=True)
    dba = models.CharField(max_length=250, blank=True,verbose_name='DBA (Doing Business AS)')
    search_keywords = models.CharField(max_length=250,verbose_name='Search Keywords', blank=True,null=True)
    language = models.ForeignKey(Languages, on_delete=models.PROTECT, null=True, blank=True, verbose_name='Language')
    website = models.CharField(max_length=250, verbose_name='website', blank=True, null=True)    
    notes = models.TextField(blank=True,max_length=300,verbose_name="Notes")

    payment_terms = models.CharField(max_length=60,
        choices=PAYMENT_TERM_CHOICES,
        default='Net 30',
        blank=True,
        null=True,
        verbose_name="Payment Terms"
    )
    house_number = models.CharField(
        max_length=100,
        verbose_name="House Number",blank=True,null=True
    )
    street_name = models.CharField(
        max_length=255,
        verbose_name="Street Name",blank=True,null=True
    )
    building_name = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name="Building Name"
    )
    landmark = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name="Landmark"
    )
    country = models.ForeignKey(Country, on_delete=models.PROTECT,  verbose_name='Country',blank=True,null=True)
    # state = models.CharField(max_length=100, verbose_name="State", blank=True, null=True)
    state = models.ForeignKey(Location, on_delete=models.PROTECT,verbose_name="State/Region",blank=True,null=True)
    sublocation = models.ForeignKey(SubLocation,on_delete=models.PROTECT,verbose_name="City/SubLocation",blank=True,null=True)
    zipcode = models.CharField(max_length=10,verbose_name="Zipcode",blank=True,null=True)
    
    maps_url = models.TextField(
        blank=True, null=True,
        verbose_name="Maps URL"
    )
    
    phone_number_1 = models.CharField(
        max_length=20,
        verbose_name="Phone Number 1",blank=True,null=True
    )
    phone_number_2 = models.CharField(
        max_length=20, blank=True, null=True,
        verbose_name="Phone Number 2"
    )
    phone_number_3 = models.CharField(
        max_length=20, blank=True, null=True,
        verbose_name="Phone Number 3"
    )
    fax = models.CharField(
        max_length=20, blank=True, null=True,
        verbose_name="Fax Number"
    )
    email_1 = models.EmailField(
       max_length=100,
        verbose_name="Email Address 1"
    )
    email_2 = models.EmailField(
        blank=True, null=True,
        verbose_name="Email Address 2"
    )
    email_3 = models.EmailField(
        blank=True, null=True,
        verbose_name="Email Address 3"
    )
    
    @property
    def get_name(self):
        return self.company_name1

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Vendor"
        verbose_name_plural = f"{verbose_name}"
        permissions = [
            ("can_create_vendor", "Can Create vendor"),
            ("can_edit_vendor", "Can can_edit vendor"),
            ("can_view_vendor", "Can View vendor"),
            ("can_delete_vendor", "Can Delete vendor"),
        ]
    
    def __str__(self):
        return f"{self.company_name1} - ({self.code})"

    def clean(self):
        # Ensure slug is unique BEFORE saving
        slug = slugify(self.company_name1)
        if Vendor.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            raise ValidationError({"company_name1": "company_name1 with this Name already exists."})

        if self.code:
            normalized_code = self.code.strip().upper()
            if Vendor.objects.exclude(pk=self.pk).filter(code=normalized_code).exists():
                raise ValidationError({"code": "Code already exists."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.company_name1)
        self.full_clean()

        if hasattr(self, "code") and self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

class VendorAttachment(VendorBaseModel,TimeStampBaseModel, UserLogBaseModel):

    class AttachmentType(models.TextChoices):
        PAN = 'PAN', 'PAN Card'
        GST = 'GST', 'GST Certificate'
        CONTRACT = 'CONTRACT', 'Contract Agreement'
        BANK_DOC = 'BANK_DOC', 'Bank Document'
        OTHER = 'OTHER', 'Other'

    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.PROTECT,
        related_name='attachments',
        verbose_name='Vendor'
    )
    attachment_type = models.CharField(
        max_length=20,
        choices=AttachmentType.choices,
        verbose_name='Attachment Type'
    )
    file = models.FileField(
        upload_to='vendor_attachments/',
        verbose_name='Attachment File'
    )
    
    notes = models.TextField(
        max_length=300,
        blank=True,
        null=True,
        verbose_name='Notes (optional)'
    )

    # def __str__(self):
    #     return f"{self.vendor.name} - {self.attachment_type}"
    
    def __str__(self):
        return f"{str(self.vendor)} - {self.attachment_type}"

    @property
    def get_name(self):
        return str(self.file)

    class Meta:
        
        verbose_name = "Vendor Attachment"
        permissions = [
            ("can_create_vendorattachment", "Can Create vendorattachment"),
            ("can_edit_vendorattachment", "Can can_edit vendorattachment"),
            ("can_view_vendorattachment", "Can View vendorattachment"),
            ("can_delete_vendorattachment", "Can Delete vendorattachment"),
        ]


class VendorBank(VendorBaseModel, TimeStampBaseModel, UserLogBaseModel):
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name='vendorbank_account')
    account_holder_name = models.CharField(max_length=100,verbose_name='Account Holder Name')
    account_number = models.CharField(max_length=10,verbose_name='Account Number', unique=True)
    routing_number = models.CharField(max_length=10,verbose_name='Routing Number')
    account_type = models.CharField(max_length=10, verbose_name='Account Type', choices=(('Savings', 'Savings'), ('Current', "Current ")))
    bank_name = models.CharField(max_length=100,verbose_name='Bank Name')
    branch_name = models.CharField(max_length=255,verbose_name='Branch Name')
    ifsc_code = models.CharField(max_length=16, verbose_name='IFSC Code')
    micr_code = models.CharField(max_length=16,   verbose_name='MICR Code')
    primary = models.BooleanField(null=True, verbose_name='Is Primary')
    swift_code = models.CharField(max_length=20,   verbose_name='SWIFT Code',  blank=True, null=True,)
    phone_number = models.CharField(max_length=16,  verbose_name='Phone Number',  blank=True, null=True,)
    address = models.CharField(max_length=255, blank=True, null=True,  verbose_name='Address')
    
   
    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"

    @property
    def get_name(self):
        return str(self.account_number)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Vendor Bank"
        permissions = [
            ("can_create_vendorbank", "Can Create vendorbank"),
            ("can_edit_vendorbank", "Can can_edit vendorbank"),
            ("can_view_vendorbank", "Can View vendorbank"),
            ("can_delete_vendorbank", "Can Delete vendorbank"),
        ]


class VendorTax(VendorBaseModel, TimeStampBaseModel, UserLogBaseModel):
    name = models.CharField(max_length=120)
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name='vendortax')
    country = models.ForeignKey(Country, on_delete=models.PROTECT,  verbose_name='Country', blank=True, null=True)
    category = models.CharField(max_length=120)
    tax_number = models.CharField(max_length=20, unique=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    other_tax_details = models.TextField(null=True)

   
    def __str__(self):
        return (self.name)

    @property
    def get_name(self):
        return str(self.name)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Vendor Tax"
        verbose_name_plural = f"{verbose_name}"
        permissions = [
            ("can_create_vendortax", "Can Create vendortax"),
            ("can_edit_vendortax", "Can can_edit vendortax"),
            ("can_view_vendortax", "Can View vendortax"),
            ("can_delete_vendortax", "Can Delete vendortax"),
        ]


class ProductVendor(VendorBaseModel,TimeStampBaseModel,UserLogBaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    @property
    def get_name(self):
        return f"{self.product.name} ↔ {self.vendor.company_name1}"   

    class Meta:
        unique_together = ("product", "vendor")
        ordering = ['-updated_at']
        verbose_name = "Product Vendor"
        verbose_name_plural = f"{verbose_name}"
        permissions = [
                ("can_create_productvendor", "Can Create productvendor"),
                ("can_edit_productvendor", "Can can_edit Productvendor"),
                ("can_view_productvendor", "Can view productvendor"),
                ("can_delete_productvendor", "Can Delete productvendor"),
            ]

    def __str__(self):
        return f"{self.product.name} ↔ {self.vendor.company_name1}"

class VendorUpload(TimeStampBaseModel,UserLogBaseModel):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    file = models.FileField(upload_to="uploads/vendors/")
    output_file = models.FileField(upload_to="uploads/output/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    total_records = models.IntegerField(default=0)
    success_records = models.IntegerField(default=0)
    failed_records = models.IntegerField(default=0)
   

    def __str__(self):
        return f"VendorUpload #{self.id}"
    class Meta:
        
        ordering = ['-updated_at']
        verbose_name = "Vendor Uploads"
        verbose_name_plural = f"{verbose_name}"
        permissions = [
                ("can_create_vendorupload", "Can Create vendorupload"),
                ("can_edit_vendorupload", "Can can_edit vendorupload"),
                ("can_view_vendorupload", "Can view vendorupload"),
                ("can_delete_vendorupload", "Can Delete vendorupload"),
            ]


auditlog.register(Vendor)
auditlog.register(VendorBank)
auditlog.register(VendorTax)
auditlog.register(VendorUpload)
auditlog.register(ProductVendor)
auditlog.register(VendorAttachment)