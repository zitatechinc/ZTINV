from django import forms
from .models import (
    Vendor, VendorType, VendorAttachment, VendorBank, VendorTax,
    ProductVendor, VendorUpload
)
from catalog.models import Product
from core.forms import VendorBaseModelForm, CodeReadonlyOnEditForm,CascadingLocationMixin
import re

phone_pattern = re.compile(r'^\d{10}$')


class BaseActiveModelForm(VendorBaseModelForm):
    """
    Base form to automatically filter ForeignKey fields to active records
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field, forms.ModelChoiceField):
                model = field.queryset.model
                if hasattr(model, 'status'):
                    field.queryset = model.objects.filter(status=1)
                elif hasattr(model, 'is_active'):
                    field.queryset = model.objects.filter(is_active=True)
                else:
                    field.queryset = model.objects.all()

class VendorModelForm(CascadingLocationMixin, BaseActiveModelForm, CodeReadonlyOnEditForm):

    class Meta:
        model = Vendor
        exclude = ('created_user', 'updated_user')

    # --- Phone validators ---
    def clean_phone_number_1(self):
        phone = self.cleaned_data.get('phone_number_1')
        if phone and not phone_pattern.match(phone):
            raise forms.ValidationError("Enter a valid 10-digit phone number.")
        return phone

    def clean_phone_number_2(self):
        phone = self.cleaned_data.get('phone_number_2')
        if phone and not phone_pattern.match(phone):
            raise forms.ValidationError("Enter a valid 10-digit phone number.")
        return phone

    def clean_phone_number_3(self):
        phone = self.cleaned_data.get('phone_number_3')
        if phone and not phone_pattern.match(phone):
            raise forms.ValidationError("Enter a valid 10-digit phone number.")
        return phone


class VendorTypeModelForm(BaseActiveModelForm, CodeReadonlyOnEditForm):
    required_css_class = 'required'
    name = forms.CharField(max_length=100)
    code = forms.CharField(max_length=100)

    class Meta:
        model = VendorType
        exclude = ('created_user', 'updated_user')


class VendorBankModelForm(BaseActiveModelForm):
    class Meta:
        model = VendorBank
        exclude = ('created_user', 'updated_user', 'vendor')


class VendorTaxModelForm(BaseActiveModelForm):
    class Meta:
        model = VendorTax
        exclude = ('created_user', 'updated_user', 'vendor')


class VendorAttachmentModelForm(BaseActiveModelForm):
    class Meta:
        model = VendorAttachment
        exclude = ('created_user', 'updated_user', 'vendor')


class ProductVendorModelForm(BaseActiveModelForm):
    vendor = forms.ModelChoiceField(
        queryset=Vendor.objects.none(),
        widget=forms.Select(attrs={"class": "form-control select2-vendor"})
    )

    class Meta:
        model = ProductVendor
        exclude = ('created_user', 'updated_user', 'product')


class VendorProductModelForm(BaseActiveModelForm):
    product = forms.ModelChoiceField(
        queryset=Product.objects.none(),
        widget=forms.Select(attrs={"class": "form-control select2-vendor"})
    )

    class Meta:
        model = ProductVendor
        exclude = ('created_user', 'updated_user', 'vendor')


class UploadFileModelForm(BaseActiveModelForm):
    class Meta:
        model = VendorUpload
        exclude = (
            'created_user', 'updated_user', 'status',
            'total_records', 'success_records',
            'failed_records', 'output_file'
        )
