from django.db import models
from django.conf import settings
from itertools import chain
import re
from utils.current_user import get_current_user
from django.core.exceptions import ValidationError




STATUS_CHOICES = (
    (1, 'Active'),
    (0, 'Draft'),
    (-1, 'Inactive'),
)

SCRAPER_STATUS_CHOICES = (
    (1, 'Success'),
    (2, 'Failed'),
)

PAYMENT_TERM_CHOICES = (
    ('Immediate', 'Immediate Payment'),
    ('Advance', 'Advance Payment'),
    ('Partial Advance', 'Partial Advance Payment'),
    ('Net 7', 'Net 7 Days'),
    ('Net 10', 'Net 10 Days'),
    ('Net 15', 'Net 15 Days'),
    ('Net 30', 'Net 30 Days'),
    ('Net 45', 'Net 45 Days'),
    ('Net 60', 'Net 60 Days'),
    ('Net 90', 'Net 90 Days'),
    ('EOM', 'End of Month'),
    ('COD', 'Cash on Delivery'),
    ('CIA', 'Cash in Advance'),
    ('2/10 Net 30', '2% Discount if paid within 10 days, else Net 30'),
    ('15 MFI', '15th of the Month Following Invoice'),
    ('30 MFI', '30th of the Month Following Invoice'),
    ('Stage Payment', 'Payment in Agreed Stages'),
    ('Milestone', 'Payment on Milestone Completion'),
    ('Upon Receipt', 'Payment Upon Receipt of Goods/Services'),
)

VENDOR_TYPE_CHOICES = (
    ('Finance Vendor', 'Finance Vendor'),
    ('Purchasing Vendor', 'Purchasing Vendor'),
    ('Service Vendor', 'Service Vendor'),
    ('Manufacturer', 'Manufacturer'),
    ('Distributor', 'Distributor'),
    ('Temporary Vendor', 'Temporary Vendor'),
    ('Internal Vendor', 'Internal Vendor'),
    ('Others', 'Others'),
)

CUSTOMER_TYPE_CHOICES = (
    ('Retail Customer', 'Retail Customer'),
    ('Wholesale Customer', 'Wholesale Customer'),
    ('Corporate Customer', 'Corporate Customer'),
    ('Government Customer', 'Government Customer'),
    ('Online Customer', 'Online Customer'),
    ('Walk-in Customer', 'Walk-in Customer'),
    ('Internal Customer', 'Internal Customer'),
    ('Others', 'Others'),
)


GM_CATEGORY_CHOICES = (
    ('RECEIPT','Receipt'),
    )

UOM_CHOICES = [
    # Basic / Each
    ('EA', 'Each'),
    ('PC', 'Piece'),
    ('SET', 'Set'),
    ('DOZ', 'Dozen'),
    ('PK', 'Pack'),
    ('BOX', 'Box'),
    ('ROL', 'Roll'),
    ('BAG', 'Bag'),
    ('PAIR', 'Pair'),

    # Weight
    ('MG', 'Milligram'),
    ('G', 'Gram'),
    ('KG', 'Kilogram'),
    ('MT', 'Metric Ton'),
    ('LB', 'Pound'),
    ('OZ', 'Ounce'),

    # Length
    ('MM', 'Millimeter'),
    ('CM', 'Centimeter'),
    ('M', 'Meter'),
    ('KM', 'Kilometer'),
    ('IN', 'Inch'),
    ('FT', 'Foot'),
    ('YD', 'Yard'),
    ('MI', 'Mile'),

    # Volume
    ('ML', 'Milliliter'),
    ('L', 'Liter'),
    ('M3', 'Cubic Meter'),
    ('GAL', 'Gallon'),
    ('QT', 'Quart'),
    ('PT', 'Pint'),
    ('CUP', 'Cup'),

    # Area
    ('MM2', 'Square Millimeter'),
    ('CM2', 'Square Centimeter'),
    ('M2', 'Square Meter'),
    ('KM2', 'Square Kilometer'),
    ('FT2', 'Square Foot'),
    ('YD2', 'Square Yard'),
    ('ACRE', 'Acre'),
    ('HA', 'Hectare'),

    # Time
    ('SEC', 'Second'),
    ('MIN', 'Minute'),
    ('HR', 'Hour'),
    ('DAY', 'Day'),
    ('WK', 'Week'),
    ('MON', 'Month'),
    ('YR', 'Year'),

    # Packaging
    ('CS', 'Case'),
    ('CTN', 'Carton'),
    ('PAL', 'Pallet'),
    ('DRM', 'Drum'),
    ('TNK', 'Tank'),
    ('BND', 'Bundle'),
    ('CAN', 'Can'),
    ('BOT', 'Bottle'),
    ('JAR', 'Jar'),
]


ITEM_STATUS_CHOICES = [
    ('AVAILABLE', 'Available'),
    ('OUT_OF_STOCK', 'Out of Stock'),
    ('RESERVED', 'Reserved'),
    ('BACKORDER', 'Backorder'),
    ('DISCONTINUED', 'Discontinued'),
    ('DAMAGED', 'Damaged'),
    ('IN_TRANSIT', 'In Transit'),
    ('PENDING', 'Pending'),
    ('OPEN','open'),
    ('CLOSED','closed')
]


FONT_SIZE_CHOICES = [(str(i), str(i)) for i in range(7, 20)]

class TimeStampBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def last_modified_at(self):
        return self.updated_at.strftime("%b,%d, %Y %H:%M") or self.created_at.strftime("%b,%d, %Y %H:%M")

    @property
    def created_date(self):
        return self.created_at.strftime("%b,%d, %Y %H:%M")

    @property
    def updated_date(self):
        return self.updated_at.strftime("%b,%d, %Y %H:%M")
    
    
    class Meta:
        abstract = True


class UserLogBaseModel(models.Model):

    created_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="%(class)s_created_by"
    )
    updated_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="%(class)s_updated_by"
    )


    class Meta:
        abstract = True

    @property
    def last_modified_user(self):
        user = self.updated_user or self.created_user
        if not user:
            return ""
        return f"{user.first_name} {user.last_name or ''}".strip()



    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and not self.pk:  # Creating
            self.created_user = user
        if user:
            self.updated_user = user
        super().save(*args, **kwargs)
   

class CatalogBaseModel(models.Model):
    name = models.CharField(
        max_length=60,
        verbose_name="Name",
        help_text="Display name"
    )
    
    code = models.CharField(
        max_length=20,
        verbose_name="Code",
        help_text="Unique identifier code",
        unique=True
    )
    status = models.IntegerField(default=0, verbose_name="Record Status", null=True, choices=STATUS_CHOICES)
    search_keywords = models.TextField(
        blank=True,
        null=True,
        verbose_name="Search Keywords",
        help_text="Search Keywords"
    )
    slug = models.SlugField(max_length=255, blank=True)
   

    @property
    def status_name(self):
        return dict(STATUS_CHOICES).get(self.status)

    @property
    def get_create_url(self):
        app_label = self._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self._meta.model_name).lower()
        return f'/{app_label}/{model_name}/create'

    @property
    def get_update_url(self):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self._meta.model_name).lower()
        return f'/{app_label}/{model_name}/{self.pk}/update'

    @property
    def get_delete_url(self):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self._meta.model_name).lower()
        return f'/{app_label}/{model_name}/{self.pk}/delete'

    @property
    def get_list_url(self):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self._meta.model_name).lower()
        return f'/{app_label}/{model_name}/{self.pk}/list'

    @property
    def get_name(self):
        return self.name

    @staticmethod
    def get_search_col_name():
        return 'company_name1'

    @staticmethod
    def get_status_col_name():
        return 'status'

    @staticmethod
    def get_search_fields():
        return ['name', "search_keywords", "code"]

    class Meta:
        abstract = True


class LocationBaseModel(TimeStampBaseModel):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Name",
        help_text="Display name"
    )
    
    code = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        verbose_name="Code",
        help_text="Unique identifier code"
    )
    status = models.IntegerField(
        choices=STATUS_CHOICES,
        default=0,
        verbose_name="Record Status",
        help_text="Current status"
    )
    slug = models.SlugField(max_length=255, unique=True,blank=True, null=True)
    @staticmethod
    def get_status_col_name():
        return 'status'

    @property
    def get_name(self):
        return self.name

    @property
    def status_name(self):
        return dict(STATUS_CHOICES).get(self.status)

    @staticmethod
    def get_search_col_name():
        return 'name'
    
    @staticmethod
    def get_search_fields():
        return ['name', "code"]

    class Meta:
        abstract = True


class VendorBaseModel(models.Model):
    status = models.IntegerField(default=0, verbose_name="Status", null=True, choices=STATUS_CHOICES)

    
    @property
    def status_name(self):
        return dict(STATUS_CHOICES).get(self.status)
    
    @staticmethod
    def get_status_col_name():
        return 'status'

    @staticmethod
    def get_search_col_name():
        return 'company_name1'

    @staticmethod
    def get_search_fields():
        return ['company_name1', "search_keywords", "vendor_type", "country__name"]

    class Meta:
        abstract = True

class ScraperBaseModel(models.Model):

    status = models.IntegerField(default=0, verbose_name="Status", null=True, choices=SCRAPER_STATUS_CHOICES)
    attachment = models.FileField(upload_to=f'product_scraper/', blank=True, null=True, verbose_name='Attachment')
    page_url = models.TextField(null=True, blank=True, verbose_name='Page URL')
    status_code = models.CharField(max_length=10, blank=True,  null=True, verbose_name='Status Code')
    payload = models.TextField(  null=True, verbose_name='Payload')
    response_data = models.TextField(null=True, verbose_name='Response Data')
    error_message = models.TextField(null=True, verbose_name='Error Message')
   

    @property
    def status_name(self):
        return dict(SCRAPER_STATUS_CHOICES).get(self.status)

    @property
    def get_create_url(self):
        app_label = self._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self._meta.model_name).lower()
        return f'/{app_label}/{model_name}/create'

    @property
    def get_update_url(self):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self._meta.model_name).lower()
        return f'/{app_label}/{model_name}/{self.pk}/update'

    @property
    def get_delete_url(self):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self._meta.model_name).lower()
        return f'/{app_label}/{model_name}/{self.pk}/delete'

    @property
    def get_list_url(self):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self._meta.model_name).lower()
        return f'/{app_label}/{model_name}/{self.pk}/list'

    @property
    def get_name(self):
        return self.id

    @staticmethod
    def get_search_col_name():
        return 'status'

    @staticmethod
    def get_status_col_name():
        return 'status'

    @staticmethod
    def get_search_fields():
        return ['status_code', "status", "id"]

    class Meta:
        abstract = True

class AttributeBaseModel(models.Model):
    name = models.CharField(
        max_length=60,
        help_text="Display name"
    )
    
    code = models.CharField(
        max_length=20,
        verbose_name="Code",
        help_text="Unique identifier code",
        unique=True
    )
    status = models.IntegerField(default=0, verbose_name="Status", null=True, choices=STATUS_CHOICES)
    search_keywords = models.TextField(
        blank=True,
        null=True,
        verbose_name="Search Keywords",
        help_text="Search Keywords"
    )
    slug = models.SlugField(max_length=255, blank=True)
    description = models.TextField(
        null=True,
        verbose_name="Description"

    )
   

    @property
    def status_name(self):
        return dict(STATUS_CHOICES).get(self.status)

    @property
    def get_create_url(self):
        app_label = self._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self._meta.model_name).lower()
        return f'/{app_label}/{model_name}/create'

    @property
    def get_update_url(self):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self._meta.model_name).lower()
        return f'/{app_label}/{model_name}/{self.pk}/update'

    @property
    def get_delete_url(self):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self._meta.model_name).lower()
        return f'/{app_label}/{model_name}/{self.pk}/delete'

    @property
    def get_list_url(self):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self._meta.model_name).lower()
        return f'/{app_label}/{model_name}/{self.pk}/list'

    @property
    def get_name(self):
        return self.name

    @staticmethod
    def get_search_col_name():
        return 'company_name1'

    @staticmethod
    def get_status_col_name():
        return 'status'

    @staticmethod
    def get_search_fields():
        return ['name', "search_keywords", "code"]

    class Meta:
        abstract = True


class InventoryBaseModel(models.Model):
    status = models.IntegerField(default=0, verbose_name="Record Status", null=True, choices=STATUS_CHOICES)
    search_keywords = models.TextField(
        blank=True,
        null=True,
        verbose_name="Search Keywords",
        help_text="Search Keywords"
    )
    description = models.TextField(blank=True,max_length=300,verbose_name="Description")
    
    @property
    def get_name(self):
        return self.code

    @property
    def status_name(self):
        return dict(STATUS_CHOICES).get(self.status)

    @property
    def get_create_url(self):
        app_label = self._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self._meta.model_name).lower()
        return f'/{app_label}/{model_name}/create'

    @property
    def get_update_url(self):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self._meta.model_name).lower()
        return f'/{app_label}/{model_name}/{self.pk}/update'

    @property
    def get_delete_url(self):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self._meta.model_name).lower()
        return f'/{app_label}/{model_name}/{self.pk}/delete'

    @property
    def get_list_url(self):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self._meta.model_name).lower()
        return f'/{app_label}/{model_name}/{self.pk}/list'

    @staticmethod
    def get_search_fields():
        return ["search_keywords", "code"]

    class Meta:
        abstract = True


class PurchaseOrderBaseModel(models.Model):
    status = models.IntegerField(default=0, verbose_name="Record Status", null=True, choices=STATUS_CHOICES)
    search_keywords = models.TextField(
        blank=True,
        null=True,
        verbose_name="Search Keywords",
        help_text="Search Keywords"
    )
    description = models.TextField(blank=True,max_length=300,verbose_name="Description")
    
    @property
    def get_name(self):
        return self.code
    
    @staticmethod
    def get_status_col_name():
        return 'status'
    
    @property
    def status_name(self):
        return dict(STATUS_CHOICES).get(self.status)

    @property
    def get_create_url(self):
        app_label = self._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self._meta.model_name).lower()
        return f'/{app_label}/{model_name}/create'

    @property
    def get_update_url(self):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self._meta.model_name).lower()
        return f'/{app_label}/{model_name}/{self.pk}/update'

    @property
    def get_delete_url(self):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self._meta.model_name).lower()
        return f'/{app_label}/{model_name}/{self.pk}/delete'

    @property
    def get_list_url(self):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self._meta.model_name).lower()
        return f'/{app_label}/{model_name}/{self.pk}/list'

    @staticmethod
    def get_search_fields():
        return ["search_keywords", "code"]

    class Meta:
        abstract = True


class CustomerBaseModel(models.Model):
    status = models.IntegerField(default=0, verbose_name="Status", null=True, choices=STATUS_CHOICES)

    
    @property
    def status_name(self):
        return dict(STATUS_CHOICES).get(self.status)
    
    @staticmethod
    def get_status_col_name():
        return 'status'

    @staticmethod
    def get_search_col_name():
        return 'company_name1'

    @staticmethod
    def get_search_fields():
        return ['company_name1', "search_keywords", "customer_type", "country__name"]

    class Meta:
        abstract = True