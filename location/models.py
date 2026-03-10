from django.db import models
from core.models import TimeStampBaseModel, UserLogBaseModel, LocationBaseModel
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from auditlog.registry import auditlog


class Country(LocationBaseModel,UserLogBaseModel):

    class Meta:
        ordering = ['name']
        verbose_name = "country"
        verbose_name_plural = "country List"
        permissions = [
            ("can_create_country", "Can Create country"),
            ("can_edit_country", "Can Edit country"),
            ("can_view_country", "Can View country"),
            ("can_delete_country", "Can Delete country"),
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
        if Country.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            raise ValidationError({"name": "Country with this Name already exists."})

        if self.code:
            normalized_code = self.code.strip().upper()
            if Country.objects.exclude(pk=self.pk).filter(code=normalized_code).exists():
                raise ValidationError({"code": "Code already exists."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.full_clean()

        if hasattr(self, "code") and self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

class Location(LocationBaseModel,UserLogBaseModel):

    country = models.ForeignKey(Country,on_delete=models.PROTECT,verbose_name='Country', blank=True, null=True)
    region = models.CharField(max_length=100,verbose_name="Region/State",help_text="Region", blank=True, null=True)
    city = models.CharField(max_length=100,verbose_name="Region/State",help_text="Region", blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Location"
        verbose_name_plural = "Location List"
        permissions = [
            ("can_create_location", "Can Create Location"),
            ("can_edit_location", "Can Edit Location"),
            ("can_view_location", "Can View Location"),
            ("can_delete_location", "Can Delete Location"),
        ]

    # def __str__(self):
    #     return f"{self.name} ({self.code})"

    def __str__(self):
        return f"{self.name}"
    
    @property
    def audit_name(self):
        return self.name

    @property
    def audit_code(self):
        return self.code
    
    def clean(self):
        # Ensure slug is unique BEFORE saving
        slug = slugify(self.name)
        if Location.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            raise ValidationError({"name": "Location with this Name already exists."})

        if self.code:
            normalized_code = self.code.strip().upper()
            if Location.objects.exclude(pk=self.pk).filter(code=normalized_code).exists():
                raise ValidationError({"code": "Code already exists."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.full_clean()

        if hasattr(self, "code") and self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

class SubLocation(LocationBaseModel,UserLogBaseModel):

    location = models.ForeignKey(Location, on_delete=models.PROTECT, verbose_name='Location Number',blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name = "SubLocation"
        verbose_name_plural = "Sub Location List"
        permissions = [
            ("can_create_sublocation", "Can Create Sub Location"),
            ("can_edit_sublocation", "Can Edit Sub Location"),
            ("can_view_sublocation", "Can View Sub Location"),
            ("can_delete_sublocation", "Can Delete Sub Location"),
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
        if SubLocation.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            raise ValidationError({"name": "SubLocation with this Name already exists."})

        if self.code:
            normalized_code = self.code.strip().upper()
            if SubLocation.objects.exclude(pk=self.pk).filter(code=normalized_code).exists():
                raise ValidationError({"code": "Code already exists."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.full_clean()

        if hasattr(self, "code") and self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

auditlog.register(Country)
auditlog.register(Location)
auditlog.register(SubLocation)