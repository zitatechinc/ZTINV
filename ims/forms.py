from django import forms
from .models import Project
from django.core.exceptions import ValidationError
from core.forms import CatalogBaseModelForm

# ---------------- ProjectHeader Form ----------------
class ProjectModelForm(CatalogBaseModelForm):
    #import pdb; pdb.set_trace();
    class Meta:
        model = Project
        exclude = ('created_at', 'updated_at')  # Excluding these fields