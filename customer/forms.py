from django import forms
from .models import Customer
from catalog.models import Languages
from location.models import Country, Location, SubLocation
from core.forms import CustomerBaseModelForm, CodeReadonlyOnEditForm, CascadingLocationMixin
import re

# Phone number validation (10-digit)
phone_pattern = re.compile(r'^\d{10}$')

class BaseActiveModelForm(CustomerBaseModelForm):
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

class CustomerModelForm(CascadingLocationMixin, BaseActiveModelForm, CodeReadonlyOnEditForm):
    class Meta:
        model = Customer
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
