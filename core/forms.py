from django import forms
from django.core.exceptions import ValidationError
import re

from location.models import Location, SubLocation

def validate_name(value):
   
    if len(value.strip()) <= 2:
        raise ValidationError("This Field at least two letters).")


def validate_code(value):
    # Allow only letters (A-Z, a-z), numbers (0-9), and hyphens (-)
    if not re.match(r'^[A-Za-z0-9]+$', value):
        raise ValidationError("This field must contain only letters and numbers.")

    # Ensure at least two characters long
    if len(value.strip()) < 2:
        raise ValidationError("This field must contain at least two letters and numbers.")


class CatalogBaseModelForm(forms.ModelForm):
    required_css_class = 'required'


    # Common init to add Bootstrap classes dynamically
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""
        for field_name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, (forms.TextInput, forms.Textarea, forms.EmailInput)):
                widget.attrs.setdefault('class', 'form-control')
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault('class', 'form-select')
    # def clean_name(self):
    #     # Check length
    #     name = self.cleaned_data.get('name')
        

    #     # Check special characters
    #     if not re.match(r'^[A-Za-z0-9 ]+$', name):
    #         raise ValidationError(f"Name can only contain letters, numbers, and spaces.")

    #     return name                

class CodeReadonlyOnEditForm(forms.ModelForm):
    """Reusable mixin to disable the 'code' field when editing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Disable 'code' field while editing existing objects
        if self.instance and self.instance.pk:
            if 'code' in self.fields:
                self.fields['code'].disabled = True
class AppBaseModelForm(forms.ModelForm):
    required_css_class = 'required'


    # Common init to add Bootstrap classes dynamically
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""
        for field_name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, (forms.TextInput, forms.Textarea, forms.EmailInput)):
                widget.attrs.setdefault('class', 'form-control')
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault('class', 'form-select')

class VendorBaseModelForm(forms.ModelForm):
    required_css_class = 'required'


    # Common init to add Bootstrap classes dynamically
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""
        for field_name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, (forms.TextInput, forms.Textarea, forms.EmailInput, forms.NumberInput)):
                widget.attrs.setdefault('class', 'form-control')
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault('class', 'form-select')


class PurchaseOrderBaseModelForm(forms.ModelForm):
    required_css_class = 'required'


    # Common init to add Bootstrap classes dynamically
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""
        for field_name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, (forms.TextInput, forms.Textarea, forms.EmailInput, forms.NumberInput)):
                widget.attrs.setdefault('class', 'form-control')
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault('class', 'form-select')

class CustomerBaseModelForm(forms.ModelForm):
    required_css_class = 'required'


    # Common init to add Bootstrap classes dynamically
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""
        for field_name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, (forms.TextInput, forms.Textarea, forms.EmailInput, forms.NumberInput)):
                widget.attrs.setdefault('class', 'form-control')
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault('class', 'form-select')


class CascadingLocationMixin:
    """
    Cascading dropdown logic.
    Works for:
    - country -> state -> sublocation (for Customer)
    - OR location -> sub_location (for ProjectHeader)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # --- Country -> State -> Sublocation (Customer) ---
        # Filter states based on selected country
        if 'country' in self.fields:
            self.fields['state'].queryset = Location.objects.none()
        if 'sublocation' in self.fields:
            self.fields['sublocation'].queryset = SubLocation.objects.none()

        country_id = None
        if 'country' in self.data:
            try:
                country_id = int(self.data.get('country'))
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and getattr(self.instance, 'country', None):
            country_id = self.instance.country.id

        # Filter states based on country
        if country_id and 'state' in self.fields:
            self.fields['state'].queryset = (
                Location.objects
                .filter(country_id=country_id, status=1)
                .order_by('name')
            )

        state_id = None
        if 'state' in self.data:
            try:
                state_id = int(self.data.get('state'))
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and getattr(self.instance, 'state', None):
            state_id = self.instance.state.id

        # Filter sublocations based on state
        if state_id and 'sublocation' in self.fields:
            self.fields['sublocation'].queryset = (
                SubLocation.objects
                .filter(location_id=state_id, status=1)
                .order_by('name')
            )


         
