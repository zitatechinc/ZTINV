# forms.py
from django import forms
from django.contrib.auth.models import Group
from .models import User
from location.models import Country
from core.forms import AppBaseModelForm, validate_name
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.forms import SetPasswordForm

class CustomLoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            "placeholder": "Username",
            "class": "form-control"
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": "Password",
            "class": "form-control"
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username", "").strip()
        password = cleaned_data.get("password", "")

        if not username or not password:
            raise forms.ValidationError("Both fields are required.")
        
        return cleaned_data

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


class UserModelForm(AppBaseModelForm):
    required_css_class = 'required'
    #group = forms.ChoiceField(choices=[(each.pk, each.name) for each in Group.objects.all()])
    groups = forms.ModelChoiceField(
        queryset=Group.objects.all(),
    widget=forms.Select(attrs={"class": "form-select"}),
    required=True,
    empty_label="Select Role",
    label="Role"
    )

    class Meta:
        model = User
        exclude=( 'date_joined', 'last_login', 'created_at', 'updated_at', 'password', 'is_staff')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            current_group = self.instance.groups.first()
            if current_group:
                self.initial['groups']= current_group
    

class ChangePasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            if field_name == 'new_password2':
                field.widget = forms.TextInput(attrs={
                    'class': 'form-control',
                    'placeholder': field.label
                })
            else:
                field.widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': field.label
                })

class ChangePasswordModelForm(AppBaseModelForm):
    required_css_class = 'required'
    new_password = forms.CharField(max_length=100, required=True)
    confirm_password = forms.CharField(max_length=100, required=True)

    # def clean_password(self):
    #     password = self.cleaned_data.get('password')
    #     validate_password(password)
    #     return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('new_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")

        return cleaned_data
    

    class Meta:
        model = User
        exclude=( 'date_joined', 'last_login', 'created_at', 
            'updated_at', 'password', 'is_staff', 'is_superuser', 'mobile_number', 'username',
            'first_name', 'last_name', 'photo', 'search_keywords'
            )
        