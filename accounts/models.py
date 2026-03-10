from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType
from core.models import STATUS_CHOICES
from django.utils import timezone
import pytz

# Create your models here.
class User(AbstractUser):
    first_name = models.CharField(max_length=100, verbose_name="First Name")
    last_name = models.CharField(max_length=100,  verbose_name="Last Name", blank=True, null=True)
    email = models.EmailField(max_length=100,  verbose_name="Email")
    mobile_number = models.CharField(max_length=20,verbose_name="Mobile Number",help_text="Mobile Number", unique=True)
    photo = models.ImageField(upload_to='accounts/',  verbose_name="Photo", help_text="Upload Photo (120x60 px)")
    date_joined = models.DateTimeField(auto_now_add=True)
    search_keywords = models.CharField(max_length=250, verbose_name="Search Keywords", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_timezone = models.CharField(
        max_length=50,
        default='UTC',
        choices=[(tz, tz) for tz in pytz.all_timezones],
         verbose_name="Timezone",
    )

    def __str__(self):
        return self.username

    @property
    def get_name(self):
        return self.username
    
    @property
    def audit_name(self):
        return self.first_name

    @property
    def audit_code(self):
        return None

    @property
    def status_name(self):
        return dict(STATUS_CHOICES).get(self.is_active)
    
    @property
    def status_col_name(self):
        return 'is_active'

    @staticmethod
    def get_search_fields():
        return ['username', "first_name", "last_name", "email", "mobile_number", 'search_keywords']

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Users"  
        verbose_name_plural = f"{verbose_name}"
        permissions = [
            ("can_create_user", "Can Create user"),
            ("can_edit_user", "Can Edit user"),
            ("can_view_user", "Can View user"),
            ("can_delete_user", "Can Delete user"),
        ]
        
