# forms.py
from django import forms
from .models import Country,Location,SubLocation
from core.forms import CatalogBaseModelForm, validate_name, validate_code,CodeReadonlyOnEditForm
import re


class CountryModelForm(CatalogBaseModelForm,CodeReadonlyOnEditForm):
    required_css_class = 'required'
    name = forms.CharField(max_length=100)
    code = forms.CharField(max_length=100)

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        # Allow only alphabets and spaces
        if not re.match(r'^[A-Za-z\s]+$', name):
            raise forms.ValidationError("Name must contain only alphabets (no numbers or special characters).")
        return name

    class Meta:
        model = Country
        exclude=('created_user', 'updated_user', 'created_at')
        
class LocationModelForm(CatalogBaseModelForm, CodeReadonlyOnEditForm):
    required_css_class = 'required'
    name = forms.CharField(max_length=100)
    code = forms.CharField(max_length=100)
    region = forms.CharField(max_length=100)
    city = forms.CharField(max_length=100)
    
    class Meta:
        model = Location
        exclude = ('created_user', 'updated_user', 'created_at')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Show only ACTIVE countries
        self.fields['country'].queryset = Country.objects.filter(status=1)

    # --- Individual Field Cleaners (Format Validation) ---

    def clean_region(self):
        region = self.cleaned_data.get('region', '').strip()
        
        if not region:
            return region
            
        # Regex allowing letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[A-Za-z\s'-]+$", region):
            raise forms.ValidationError(
                "Region/State name must contain only letters, spaces, hyphens, or apostrophes."
            )
        
        return region.title() # Format nicely

    def clean_city(self):
        city = self.cleaned_data.get('city', '').strip()
        
        if not city:
            return city
            
        if not re.match(r"^[A-Za-z\s'-]+$", city):
            raise forms.ValidationError(
                "City name must contain only letters, spaces, hyphens, or apostrophes."
            )
        
        return city.title() 

    def clean(self):
        # This method runs AFTER individual field cleaners (clean_city, clean_region, etc.)
        cleaned_data = super().clean()
        country = cleaned_data.get("country")
        region = cleaned_data.get("region")
        city = cleaned_data.get("city")

        # Rule 1: Cannot specify a Region/State without a Country
        if region and not country:
             # Add error specifically to the region field
             self.add_error('region', "You must select a Country when providing a Region/State.")

        # Rule 2: Cannot specify a City without a Region/State AND a Country
        if city and (not country or not region):
             # Add error specifically to the city field
             self.add_error('city', "You must provide both a Country and a Region/State when providing a City.")

        return cleaned_data

class SubLocationModelForm(CatalogBaseModelForm, CodeReadonlyOnEditForm):
    required_css_class = 'required'
    name = forms.CharField(max_length=100)
    code = forms.CharField(max_length=100)
    
    #location = forms.ModelChoiceField(queryset=Location.objects.all(), required=True, label='Location') # diaply all location
    location = forms.ModelChoiceField(
    queryset=Location.objects.filter(status=1),required=True,label='Location')  # display only Active locations


    class Meta:
        model = SubLocation
        exclude = ('created_user', 'updated_user', 'created_at')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        qs = Location.objects.filter(status=1)

        if self.instance.pk and self.instance.location:
            qs = qs | Location.objects.filter(pk=self.instance.location.pk)

        self.fields['location'].queryset = qs.distinct()

    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not re.match(r"^[A-Za-z0-9\s'-]+$", name):
            raise forms.ValidationError("Code must contain only letters, numbers, spaces, hyphens, or apostrophes.")

        return name
    
    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip()

        if not re.match(r"^[A-Za-z0-9\s'-]+$", code):
            raise forms.ValidationError(
                "Code must contain only letters, numbers, spaces, hyphens, or apostrophes."
            )
        
        return code.upper()  # Normalize to uppercase

    def clean(self):
        cleaned_data = super().clean()
        location = cleaned_data.get("location")
        name = cleaned_data.get("name")
        
        # Rule 1: Ensure Sublocation name is unique within the given location
        if location and name:
            if SubLocation.objects.exclude(pk=self.instance.pk).filter(location=location, name=name).exists():
                self.add_error('name', f"A Sublocation with the name '{name}' already exists in this location.")
        
        return cleaned_data

