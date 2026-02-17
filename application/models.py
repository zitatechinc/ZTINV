from django.db import models
from core.models import UserLogBaseModel, TimeStampBaseModel, STATUS_CHOICES, FONT_SIZE_CHOICES
from auditlog.models import LogEntry
from auditlog.registry import auditlog

FONT_CHOICES = [
   
    ('"Segoe UI", SegoeUI, "Helvetica Neue", Helvetica, Arial, sans-serif','"Segoe UI", SegoeUI, "Helvetica Neue", Helvetica, Arial, sans-serif')
]

class Themes(UserLogBaseModel, TimeStampBaseModel):
    name = models.CharField(max_length=250, unique=True, verbose_name="Theme Name")
    bg_color = models.CharField(max_length=30, default='#f5f6fe', verbose_name="BG Color")
    font_family = models.CharField(
        choices=FONT_CHOICES,
        max_length=100,
        default='"Segoe UI", SegoeUI, "Helvetica Neue", Helvetica, Arial, sans-serif',
        verbose_name="Font Family"
    )
    
    heading_font_color = models.CharField(max_length=30, default='#555', verbose_name="Heading Font Color")
    page_title_font_color = models.CharField(max_length=30, default='#555', verbose_name="Page Title Font Color")
    menu_bg_color = models.CharField(max_length=30, default='#fafafa', verbose_name="Menu BG Color")
    menu_font_color = models.CharField(max_length=30, default='#555', verbose_name="Menu Font Color")

    sidebar_bg_color = models.CharField(max_length=30, default='#fafafa', verbose_name="Sidebar BG Color")
    sidebar_font_color = models.CharField(max_length=30, default='#555', verbose_name="Sidebar Font Color")

    footer_bg_color = models.CharField(max_length=30, default='#fafafa', verbose_name="Footer BG Color")
    footer_font_color = models.CharField(max_length=30, default='#555', verbose_name="Footer Font Color")

    status = models.IntegerField(default=0, verbose_name="Status", null=True, choices=STATUS_CHOICES)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Theme"
        verbose_name_plural = "Theme"
        permissions = [
            ("can_create_themes", "Can Create themes"),
            ("can_edit_themes", "Can Edit themes"),
            ("can_view_themes", "Can View themes"),
            ("can_delete_themes", "Can Delete theme"),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"

    @property
    def get_name(self):
        return self.name

    @staticmethod
    def get_search_col_name():
        return 'name'

    @staticmethod
    def get_search_fields():
        return ['name']



class AppSettings(UserLogBaseModel, TimeStampBaseModel):
    name = models.CharField(max_length=250, unique=True, verbose_name="Application Name")
    company_name = models.CharField(max_length=250, verbose_name="Company Name", unique=True,)
    email = models.CharField(max_length=250, null=True, blank=True, verbose_name=" Email")
    phone = models.CharField(max_length=250, null=True, blank=True, verbose_name="Phone Number")
    website = models.CharField(max_length=250, null=True, blank=True, verbose_name="Website")
    address = models.TextField(blank=True, help_text="address", verbose_name="Address")

    logo = models.ImageField(upload_to='application/',  verbose_name="Logo", help_text="Upload logo (120x60 px)")
    favicon = models.ImageField(upload_to='application/',  verbose_name="Favicon", help_text="Upload favicon icon")
    header_text = models.TextField(blank=True, help_text="Header Text", verbose_name="Header Text")
    footer_text = models.TextField(blank=True, help_text="Footer Text", verbose_name="Footer Text")
    theme = models.ForeignKey(Themes, on_delete=models.PROTECT,default=1)

    # attribute_1 = models.CharField(max_length=250,  verbose_name="Field 1", null=True, blank=True)
    # attribute_2 = models.CharField(max_length=250,  verbose_name="Field 2", null=True, blank=True)
    # attribute_3 = models.CharField(max_length=250, verbose_name="Field 3", null=True, blank=True)
    # attribute_4 = models.CharField(max_length=250,  verbose_name="Field 4",  null=True, blank=True)
    # attribute_5 = models.CharField(max_length=250,  verbose_name="Field 5",  null=True, blank=True)
    # attribute_6 = models.CharField(max_length=250,  verbose_name="Field 6",  null=True, blank=True)


    class Meta:
        ordering = ['-updated_at']
        verbose_name = "App Settings"
        verbose_name_plural = "App Settings"
        permissions = [
            ("can_create_appsettings", "Can Create appsettings"),
            ("can_edit_appsettings", "Can Edit appsettings"),
            ("can_view_appsettings", "Can View appsettings"),
            ("can_delete_appsettings", "Can Delete appsettings"),
        ]

    def __str__(self):
        return f"{self.name}"

    @property
    def get_name(self):
        return self.name

    @staticmethod
    def get_search_col_name():
        return 'name'

    @staticmethod
    def get_search_fields():
        return ['name', "company_name"]




auditlog.register(Themes)
auditlog.register(AppSettings)