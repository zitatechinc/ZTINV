# forms.py
from django import forms
from .models import Themes, AppSettings
from location.models import Country
from core.forms import AppBaseModelForm, validate_name


class ThemeModelForm(AppBaseModelForm):
    required_css_class = 'required'
    name = forms.CharField(max_length=100, validators=[validate_name])

    class Meta:
        model = Themes
        exclude=('created_user', 'updated_user')

class AppSettingsModelForm(AppBaseModelForm):
    required_css_class = 'required'
    name = forms.CharField(max_length=100, validators=[validate_name])
    company_name = forms.CharField(max_length=100, validators=[validate_name])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load only active themes
        self.fields['theme'].queryset = Themes.objects.filter(status=True)

    class Meta:
        model = AppSettings 
        exclude=('created_user', 'updated_user')

