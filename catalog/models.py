from django.db import models
from core.models import CatalogBaseModel,UserLogBaseModel, TimeStampBaseModel, ScraperBaseModel,AttributeBaseModel, UOM_CHOICES
from location.models import Country
import json
from django.core.exceptions import ValidationError
from auditlog.registry import auditlog
from django.utils.text import slugify

SERIALIZED_STATUS_CHOICES = (
    (1, 'Yes'),
    (0, 'No'),  
)

class Category(CatalogBaseModel,UserLogBaseModel, TimeStampBaseModel):
    parent = models.ForeignKey('self', null=True, blank=True, related_name='subcategories', on_delete=models.PROTECT)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Category"
        verbose_name_plural = f"{verbose_name} List"
        permissions = [
            ("can_create_category", "Can Create Category"),
            ("can_edit_category", "Can Edit Category"),
            ("can_view_category", "Can View Category"),
            ("can_delete_category", "Can Delete Category"),
            ("can_history_category", "Can History Category"),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def audit_name(self):
        return self.name

    @property
    def audit_code(self):
        return self.code

    def clean(self):
        # Ensure slug is unique BEFORE saving
        slug = slugify(self.name)
        if Category.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            raise ValidationError({"name": "Category with this Name already exists."})

        if self.code:
            normalized_code = self.code.strip().upper()
            if Category.objects.exclude(pk=self.pk).filter(code=normalized_code).exists():
                raise ValidationError({"code": "Code already exists."})
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.full_clean()

        if hasattr(self, "code") and self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)
        
class ProductType(CatalogBaseModel,UserLogBaseModel, TimeStampBaseModel):
    
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Product Type"
        verbose_name_plural = f"{verbose_name} List"
        permissions = [
            ("can_create_producttype", "Can Create product_type"),
            ("can_edit_producttype", "Can Edit product_type"),
            ("can_view_producttype", "Can View product_type"),
            ("can_delete_producttype", "Can Delete product_type"),
        ]


    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def audit_name(self):
        return self.name

    @property
    def audit_code(self):
        return self.code

    def clean(self):
        # Ensure slug is unique BEFORE saving
        slug = slugify(self.name)
        if ProductType.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            raise ValidationError({"name": "ProductType with this Name already exists."})

        if self.code:
            normalized_code = self.code.strip().upper()
            if ProductType.objects.exclude(pk=self.pk).filter(code=normalized_code).exists():
                raise ValidationError({"code": "Code already exists."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.full_clean()

        if hasattr(self, "code") and self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

class ProductGroup(CatalogBaseModel,UserLogBaseModel, TimeStampBaseModel):
    
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Product Group"
        verbose_name_plural = f"{verbose_name} List"
        permissions = [
            ("can_create_productgroup", "Can Create Product Group"),
            ("can_edit_productgroup", "Can Edit Product Group"),
            ("can_view_productgroup", "Can View Product Group"),
            ("can_delete_productgroup", "Can Delete Product Group"),
        ]


    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def audit_name(self):
        return self.name

    @property
    def audit_code(self):
        return self.code

    def clean(self):
        # Ensure slug is unique BEFORE saving
        slug = slugify(self.name)
        if ProductGroup.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            raise ValidationError({"name": "ProductGroup with this Name already exists."})

        if self.code:
            normalized_code = self.code.strip().upper()
            if ProductGroup.objects.exclude(pk=self.pk).filter(code=normalized_code).exists():
                raise ValidationError({"code": "Code already exists."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.full_clean()

        if hasattr(self, "code") and self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

ATTRIBUTE_TYPE_CHOICES = (("Common", "Common"), ("Category Specific", "Category Specific"))
class Attribute(AttributeBaseModel,UserLogBaseModel, TimeStampBaseModel):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, null=True, verbose_name='Category Name', blank=True)
    product_type = models.ForeignKey(ProductType, on_delete=models.PROTECT,  null=True, verbose_name='Product Type', blank=True)
    product_group = models.ForeignKey(ProductGroup, on_delete=models.PROTECT, null=True, verbose_name='Product Group', blank=True)
    attribute_type = models.CharField(max_length=100, verbose_name='Attribute Type', help_text='Attribute Type.', choices=ATTRIBUTE_TYPE_CHOICES)
    class Meta:
        unique_together = [['name', 'category', 'product_type','product_group']]
        ordering = ['id']
        verbose_name = "Attribute"
        verbose_name_plural = f"{verbose_name} List"
        permissions = [
            ("can_create_attribute", "Can Create attributes"),
            ("can_edit_attribute", "Can Edit attributes"),
            ("can_view_attribute", "Can View attributes"),
            ("can_delete_attribute", "Can Delete attributes"),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def audit_name(self):
        return self.name

    @property
    def audit_code(self):
        return self.code

    def clean(self):
        slug = slugify(self.name)
        if Attribute.objects.exclude(pk=self.pk).filter(slug=slug,category=self.category,product_type=self.product_type,product_group=self.product_group).exists():
            raise ValidationError({"name": "Attribute with this Name already exists."})

        if self.code:
            normalized_code = self.code.strip().upper()
            if ProductGroup.objects.exclude(pk=self.pk).filter(code=normalized_code).exists():
                raise ValidationError({"code": "Code already exists."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.full_clean()

        if hasattr(self, "code") and self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

class Brand(CatalogBaseModel,UserLogBaseModel, TimeStampBaseModel):
    description = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Brand"
        verbose_name_plural = f"{verbose_name}"
        permissions = [
            ("can_create_brand", "Can Create brand"),
            ("can_edit_brand", "Can Edit brand"),
            ("can_view_brand", "Can View brand"),
            ("can_delete_brand", "Can Delete brand"),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def audit_name(self):
        return self.name

    @property
    def audit_code(self):
        return self.code

    def clean(self):
        # Ensure slug is unique BEFORE saving
        slug = slugify(self.name)
        if Brand.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            raise ValidationError({"name": "Brand with this Name already exists."})

        if self.code:
            normalized_code = self.code.strip().upper()
            if Brand.objects.exclude(pk=self.pk).filter(code=normalized_code).exists():
                raise ValidationError({"code": "Code already exists."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.full_clean()

        if hasattr(self, "code") and self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

class Manufacturer(CatalogBaseModel,UserLogBaseModel, TimeStampBaseModel):
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Manufacturer"
        verbose_name_plural = f"{verbose_name}"
        permissions = [
            ("can_create_manufacturer", "Can Create manufacturer"),
            ("can_edit_manufacturer", "Can Edit manufacturer"),
            ("can_view_manufacturer", "Can View manufacturer"),
            ("can_delete_manufacturer", "Can Delete manufacturer"),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def audit_name(self):
        return self.name

    @property
    def audit_code(self):
        return self.code

    def clean(self):
        # Ensure slug is unique BEFORE saving
        slug = slugify(self.name)
        if Manufacturer.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            raise ValidationError({"name": "Manufacturer with this Name already exists."})

        if self.code:
            normalized_code = self.code.strip().upper()
            if Manufacturer.objects.exclude(pk=self.pk).filter(code=normalized_code).exists():
                raise ValidationError({"code": "Code already exists."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.full_clean()

        if hasattr(self, "code") and self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

class Languages(CatalogBaseModel,UserLogBaseModel, TimeStampBaseModel):

    class Meta:
        ordering = ['name']
        verbose_name = "Language"
        verbose_name_plural = f"{verbose_name} List"
        permissions = [
            ("can_create_languages", "Can Create languages"),
            ("can_edit_languages", "Can Edit languages"),
            ("can_view_languages", "Can View languages"),
            ("can_delete_languages", "Can Delete languages"),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def audit_name(self):
        return self.name

    @property
    def audit_code(self):
        return self.code

    def clean(self):
        # Ensure slug is unique BEFORE saving
        slug = slugify(self.name)
        if Languages.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            raise ValidationError({"name": "Languages with this Name already exists."})

        if self.code:
            normalized_code = self.code.strip().upper()
            if Languages.objects.exclude(pk=self.pk).filter(code=normalized_code).exists():
                raise ValidationError({"code": "Code already exists."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.full_clean()

        if hasattr(self, "code") and self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

class Product(CatalogBaseModel,UserLogBaseModel, TimeStampBaseModel):
    # Note : Material Code nothing but code and Product Description nothing but name 
    category = models.ForeignKey(Category, on_delete=models.PROTECT, null=True, verbose_name='Category Name')
    product_type = models.ForeignKey(ProductType, on_delete=models.PROTECT,  null=True, verbose_name='Product Type')
    product_group = models.ForeignKey(ProductGroup, null=True, on_delete=models.PROTECT,  verbose_name='Product Group')
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, blank=True,null=True, verbose_name='Brand Name')
    manufacturer = models.ForeignKey(Manufacturer,  on_delete=models.PROTECT, null=True, verbose_name='Manufacturer Name')
    language = models.ForeignKey(Languages, on_delete=models.PROTECT,blank=True, null=True, verbose_name='Language')
    country = models.ForeignKey(Country, on_delete=models.PROTECT, blank=True,null=True, verbose_name='Country Origin')
    unit_of_measure = models.ForeignKey('ims.Units', on_delete=models.PROTECT,verbose_name='Unit of Measure')
    procurementtype = models.ForeignKey('ims.ProcurementType',  on_delete=models.PROTECT,verbose_name='Procurement Type')
    specification = models.CharField(max_length=100, verbose_name='Product Specification')
    model_number = models.CharField(max_length=25, verbose_name='Part No/Drawing No')
    source_of_make = models.CharField(max_length=25,verbose_name='Make')
    
    long_description = models.TextField(blank=True, verbose_name='Long Description')
    short_description = models.TextField(blank=True, verbose_name='Short Description')
    notes = models.TextField(blank=True, verbose_name='Notes')
    # upload columns
    image = models.ImageField(upload_to=f'products/', blank=True, null=True, verbose_name='Product Image')
    file = models.FileField(upload_to=f'products/',blank=True, null=True, verbose_name='Specification File')
    # Optional columns for Future requirements
    serialnumber_status = models.IntegerField(default=0, verbose_name="Serial Number Status", null=True, choices=SERIALIZED_STATUS_CHOICES)
    prefix = models.CharField(max_length=120, blank=True,  null=True, verbose_name='Serial Number Prefix')
    material_code = models.CharField(max_length=25, blank=True, null=True,  verbose_name='Material Code')
    mpin = models.CharField(max_length=12, blank=True, null=True, verbose_name='MPIN', help_text='Enter your 4-digit MPIN for secure transactions.')
    upc = models.CharField(max_length=4, blank=True, null=True, verbose_name='UPC', help_text='Enter the 4-digit Universal Product Code (UPC).')
    isbn = models.CharField(max_length=120, blank=True, null=True, verbose_name='ISBN')
    ean = models.CharField(max_length=13, blank=True,  null=True, verbose_name='EAN', help_text='Enter the 13-digit European Article Number (EAN).')
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Product"
        verbose_name_plural = f"{verbose_name} List"
        permissions = [
            ("can_create_product", "Can Create product"),
            ("can_edit_product", "Can Edit product"),
            ("can_view_product", "Can View product"),
            ("can_delete_product", "Can Delete product"),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def audit_name(self):
        return self.name

    @property
    def audit_code(self):
        return self.code
    
    def display_name(self):
        return self.name.title()
    
    def getProductLinks(self):
        return ProductLinks.objects.filter(product_id=self.pk)
    
    def getProductAttributes(self):
        return ProductAttribute.objects.filter(product_id=self.pk)

    def clean(self):
        # Ensure slug is unique BEFORE saving
        slug = slugify(self.name)
        if Product.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            raise ValidationError({"name": "Product with this Name already exists."})

        if self.code:
            normalized_code = self.code.strip().upper()
            if Product.objects.exclude(pk=self.pk).filter(code=normalized_code).exists():
                raise ValidationError({"code": "Code already exists."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.full_clean()

        if hasattr(self, "code") and self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

class ProductLinks(TimeStampBaseModel, UserLogBaseModel):
    url = models.TextField(blank=True)
    product = models.ForeignKey(Product, related_name='ProductLinks', on_delete=models.PROTECT)
    
    class Meta:
        ordering = ['id']
        verbose_name = "Product Attributes"
        verbose_name_plural = f"{verbose_name} List"
        permissions = [
            ("can_create_productlinks", "Can Create product_links"),
            ("can_edit_productlinks", "Can Edit product_links"),
            ("can_view_productlinks", "Can View product_links"),
            ("can_delete_productlinks", "Can Delete product_links"),
        ]
    
class ProductAttribute(TimeStampBaseModel, UserLogBaseModel):
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    attribute = models.ForeignKey(Attribute, on_delete=models.PROTECT)
    value = models.TextField()

    class Meta:
        ordering = ['id']
        verbose_name = "Product Attribute"
        verbose_name_plural = f"{verbose_name} List"
        permissions = [
            ("can_create_productattribute", "Can Create productattribute"),
            ("can_edit_productattribute", "Can Edit productattribute"),
            ("can_view_productattribute", "Can View productattribute"),
            ("can_delete_productattribute", "Can Delete productattribute"),
        ]

    def getProductAttributes(self):
        return ProductAttribute.objects.filter(product_id=self.pk)
        
    def __str__(self):
       return f"{self.attribute.name} ({self.value})"
    
    @property
    def audit_name(self):
        return self.attribute.name

    @property
    def audit_code(self):
        return None
    
    # def __str__(self):
    #     return f"{self.name} ({self.code})"

class ProductUpload(TimeStampBaseModel,UserLogBaseModel):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    file = models.FileField(upload_to="uploads/product/")
    output_file = models.FileField(upload_to="uploads/output/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    total_records = models.IntegerField(default=0)
    success_records = models.IntegerField(default=0)
    failed_records = models.IntegerField(default=0)
   
    def __str__(self):
        return f"ProductUpload #{self.id}"
    
    @property
    def audit_name(self):
        return f"ProductUpload #{self.id}"

    @property
    def audit_code(self):
        return None

    @staticmethod
    def get_status_col_name():
        return "status"
    
    class Meta:
        
        ordering = ['-updated_at']
        verbose_name = "Product Uploads"
        verbose_name_plural = f"{verbose_name}"
        permissions = [
                ("can_create_productupload", "Can Create productupload"),
                ("can_edit_productupload", "Can can_edit productupload"),
                ("can_view_productupload", "Can view productupload"),
                ("can_delete_productupload", "Can Delete productupload"),
            ]

            
auditlog.register(Product)
auditlog.register(Category)
auditlog.register(ProductType)
auditlog.register(ProductGroup)
auditlog.register(Attribute)
auditlog.register(Manufacturer)
auditlog.register(Languages)
auditlog.register(ProductAttribute)
auditlog.register(Brand)
auditlog.register(ProductLinks)
auditlog.register(ProductUpload)
