# forms.py
from django import forms
from .models import Category, ProductType, Product, ProductLinks, Brand, Manufacturer, Languages, Attribute,ProductGroup,ProductUpload, ProductAttribute
from location.models import Country
from itertools import chain
from core.forms import CatalogBaseModelForm, validate_name, validate_code,CodeReadonlyOnEditForm,CodeReadonlyOnEditForm
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
import re


class CategoryModelForm(CatalogBaseModelForm, CodeReadonlyOnEditForm):

    required_css_class = 'required'
    name = forms.CharField(max_length=250)
    code = forms.CharField(max_length=100)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show only active parent categories
        qs = Category.objects.filter(status=1).order_by('name')
        # Include current parent even if inactive (for editing)
        if self.instance.pk and self.instance.parent:
            qs = qs | Category.objects.filter(pk=self.instance.parent.pk)
        self.fields['parent'].queryset = qs.distinct()

    class Meta:
        model = Category
        exclude = ('created_user', 'updated_user')

class BrandModelForm(CatalogBaseModelForm, CodeReadonlyOnEditForm):
    required_css_class = 'required'
    name = forms.CharField(max_length=100)
    code = forms.CharField(max_length=100)

    class Meta:
        model = Brand
        exclude=('created_user', 'updated_user')

class ManufacturerModelForm(CatalogBaseModelForm, CodeReadonlyOnEditForm):
    required_css_class = 'required'
    name = forms.CharField(max_length=100)
    code = forms.CharField(max_length=100)

    # def clean_name(self):
    #     name = self.cleaned_data.get('name', '').strip()
        
    class Meta:
        model = Manufacturer
        exclude=('created_user', 'updated_user')

class ProductTypeModelForm(CatalogBaseModelForm, CodeReadonlyOnEditForm):
    required_css_class = 'required'
    name = forms.CharField(max_length=100)
    code = forms.CharField(max_length=100)

    class Meta:
        model = ProductType
        exclude=('created_user', 'updated_user')

class AttributesModelForm(CatalogBaseModelForm, CodeReadonlyOnEditForm):

    required_css_class = 'required'
    name = forms.CharField(max_length=100)
    code = forms.CharField(max_length=100)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Show only active records
        self.fields["category"].queryset = Category.objects.filter(status=1).order_by('name')
        self.fields["product_type"].queryset = ProductType.objects.filter(status=1).order_by('name')
        self.fields["product_group"].queryset = ProductGroup.objects.filter(status=1).order_by('name')

        # Include current selections for editing even if inactive
        if self.instance.pk:
            if self.instance.category:
                self.fields["category"].queryset |= Category.objects.filter(pk=self.instance.category.pk)
            if self.instance.product_type:
                self.fields["product_type"].queryset |= ProductType.objects.filter(pk=self.instance.product_type.pk)
            if self.instance.product_group:
                self.fields["product_group"].queryset |= ProductGroup.objects.filter(pk=self.instance.product_group.pk)

    class Meta:
        model = Attribute
        exclude = ('created_user', 'updated_user')

class LanguagesModelForm(CatalogBaseModelForm,CodeReadonlyOnEditForm):
    required_css_class = 'required'
    name = forms.CharField(max_length=100)
    code = forms.CharField(max_length=100)

    # def clean_name(self):
    #     name = self.cleaned_data.get('name', '').strip()
    #     if not re.match(r'^[A-Za-z\s]+$', name):
    #         raise forms.ValidationError("Name must contain only alphabets and spaces.")
    #     return name

    # def clean_code(self):
    #     # Check length
    #     code = self.cleaned_data.get('code')
        
    #     # Check special characters
    #     if not re.match(r'^[A-Za-z0-9 ]+$', code):
    #         raise ValidationError("Language code can only contain letters, numbers, and spaces.")
    #     return code   

    class Meta:
        model = Languages
        exclude=('created_user', 'updated_user')

class ProductModelForm(CatalogBaseModelForm, CodeReadonlyOnEditForm):
    required_css_class = 'required'
    name = forms.CharField(max_length=100)
    code = forms.CharField(max_length=100)
    url = forms.CharField(max_length=500, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active categories in dropdown
        self.fields["category"].queryset = Category.objects.filter(status=1).order_by('name')
        self.fields["manufacturer"].queryset = Manufacturer.objects.filter(status=1).order_by('name')
        self.fields["brand"].queryset = Brand.objects.filter(status=1).order_by('name')
        self.fields["language"].queryset = Languages.objects.filter(status=1).order_by('name')
        self.fields["product_type"].queryset = ProductType.objects.filter(status=1).order_by('name')
        self.fields["product_group"].queryset = ProductGroup.objects.filter(status=1).order_by('name')
        self.fields["country"].queryset = Country.objects.filter(status=1).order_by('name')
        self.fields['serialnumber_status'].disabled = True

    class Meta:
        model = Product
        exclude=('created_user', 'updated_user','upc','isbn','ean','mpin','material_code')
       
class ProductLinksModelForm(CatalogBaseModelForm):
    required_css_class = 'required'

    class Meta:
        model = ProductLinks
        exclude=('created_user', 'updated_user', 'product')

class ProductUploadFileModelForm(CatalogBaseModelForm):
    
    class Meta:
        model = ProductUpload
        exclude =('created_user', 'updated_user','status','total_records','success_records','failed_records','output_file')

class ProductGroupModelForm(CatalogBaseModelForm, CodeReadonlyOnEditForm):
    required_css_class = 'required'
    name = forms.CharField(max_length=100)
    code = forms.CharField(max_length=100)

    class Meta:
        model = ProductGroup
        exclude=('created_user', 'updated_user') 

class ProductAttributeModelForm(CatalogBaseModelForm):
    def __init__(self,product_id=None,*args, **kwargs):

        super().__init__(*args, **kwargs)
        self.product_id = product_id
        
        product_obj = Product.objects.get(pk=self.product_id)
        attributes = Attribute.objects.filter(status=True,category=product_obj.category,product_type=product_obj.product_type,product_group=product_obj.product_group).order_by('name')

        for attr in attributes:
            existing_value = ProductAttribute.objects.filter(attribute=attr,product=product_obj).first()
            self.fields[f"attr_{attr.pk}"] = forms.CharField(
                label=attr.name.upper(),
                initial=existing_value.value if existing_value else "",
                required=False,
                widget=forms.TextInput(attrs={"class": "form-control", "data_type" : attr.attribute_type})
            )  
    class Meta:
        model = ProductAttribute
        exclude=('created_user', 'updated_user','product','attribute','value')
