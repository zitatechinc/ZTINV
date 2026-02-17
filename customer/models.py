from django.db import models
from core.models import TimeStampBaseModel, CustomerBaseModel, UserLogBaseModel
from location.models import Country, Location, SubLocation
from accounts.models import User
from catalog.models import  Languages
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from core.models import CUSTOMER_TYPE_CHOICES, STATUS_CHOICES, PAYMENT_TERM_CHOICES
from auditlog.registry import auditlog
        
class Customer(CustomerBaseModel, TimeStampBaseModel, UserLogBaseModel):
    code = models.CharField(
        max_length=100,
        verbose_name="Code",
        help_text="Unique identifier code",
        unique=True
    )
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    customer_type = models.CharField(max_length=60,verbose_name="Customer Type", choices=CUSTOMER_TYPE_CHOICES)
    company_name1 = models.CharField(max_length=250, verbose_name='Company Name1', unique=True)
    company_name2 = models.CharField(max_length=250, verbose_name='Company Name2',blank=True,null=True)
    dba = models.CharField(max_length=250, blank=True,verbose_name='DBA (Doing Business AS)')
    search_keywords = models.CharField(max_length=250,verbose_name='Search Keywords',blank=True,null=True)
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
    country = models.ForeignKey(Country, on_delete=models.PROTECT,  verbose_name='Country')
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
        verbose_name = "Customer"
        verbose_name_plural = f"{verbose_name}"
        permissions = [
            ("can_create_customer", "Can Create customer"),
            ("can_edit_customer", "Can can_edit customer"),
            ("can_view_customer", "Can View customer"),
            ("can_delete_customer", "Can Delete customer"),
        ]
    

    def __str__(self):
        return f"{self.company_name1} - ({self.code})"

    def clean(self):
        # Ensure slug is unique BEFORE saving
        slug = slugify(self.company_name1)
        if Customer.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            raise ValidationError({"company_name1": "company_name1 with this Name already exists."})

        if self.code:
            normalized_code = self.code.strip().upper()
            if Customer.objects.exclude(pk=self.pk).filter(code=normalized_code).exists():
                raise ValidationError({"code": "Code already exists."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.company_name1)
        self.full_clean()

        if hasattr(self, "code") and self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

auditlog.register(Customer)