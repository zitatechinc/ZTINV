# catalog/management/commands/insert_default_themes.py
import random
from django.core.management.base import BaseCommand
from application.models import Themes  # adjust import if your Themes model is in a different app

class Command(BaseCommand):
    help = 'Insert default/best theme details into the database'

    def handle(self, *args, **kwargs):
        themes_data = [
            {
                "name": "Modern Light",
                "bg_color": "#f4f6f9",
                "font_family": '"Segoe UI", SegoeUI, "Helvetica Neue", Helvetica, Arial, sans-serif',
                "heading_font_color": "#2c3e50",
                "page_title_font_color": "#34495e",
                "menu_bg_color": "#ffffff",
                "menu_font_color": "#2c3e50",
                "sidebar_bg_color": "#2f4050",
                "sidebar_font_color": "#ecf0f1",
                "footer_bg_color": "#f4f6f9",
                "footer_font_color": "#7f8c8d",
                "status": 1,
            },
            {
                "name": "Dark Mode",
                "bg_color": "#1f1f2e",
                "font_family": '"Roboto", "Helvetica Neue", Arial, sans-serif',
                "heading_font_color": "#ecf0f1",
                "page_title_font_color": "#bdc3c7",
                "menu_bg_color": "#2c3e50",
                "menu_font_color": "#ecf0f1",
                "sidebar_bg_color": "#34495e",
                "sidebar_font_color": "#ecf0f1",
                "footer_bg_color": "#2c3e50",
                "footer_font_color": "#bdc3c7",
                "status": 1,
            },
            {
                "name": "Minimal White",
                "bg_color": "#ffffff",
                "font_family": '"Open Sans", Arial, sans-serif',
                "heading_font_color": "#2c3e50",
                "page_title_font_color": "#34495e",
                "menu_bg_color": "#f8f9fa",
                "menu_font_color": "#2c3e50",
                "sidebar_bg_color": "#f8f9fa",
                "sidebar_font_color": "#2c3e50",
                "footer_bg_color": "#ffffff",
                "footer_font_color": "#7f8c8d",
                "status": 1,
            },
            {
                "name": "Blue Gradient",
                "bg_color": "#e0f7fa",
                "font_family": '"Segoe UI", SegoeUI, "Helvetica Neue", Helvetica, Arial, sans-serif',
                "heading_font_color": "#0d47a1",
                "page_title_font_color": "#1565c0",
                "menu_bg_color": "#2196f3",
                "menu_font_color": "#ffffff",
                "sidebar_bg_color": "#1565c0",
                "sidebar_font_color": "#ffffff",
                "footer_bg_color": "#e0f7fa",
                "footer_font_color": "#0d47a1",
                "status": 1,
            },
            {
            "name": "Professional Blue",
            "bg_color": "#f5f7fa",  # light, clean background
            "font_family": '"Segoe UI", Roboto, "Helvetica Neue", Helvetica, Arial, sans-serif',
            "heading_font_color": "#1a1a2e",  # dark blue-black for headings
            "page_title_font_color": "#162447",
            "menu_bg_color": "#1f4068",  # deep blue menu
            "menu_font_color": "#ffffff",  # white text on menu
            "sidebar_bg_color": "#1b1b2f",  # dark sidebar
            "sidebar_font_color": "#ffffff",  # readable white text
            "footer_bg_color": "#e4e9f2",  # subtle footer
            "footer_font_color": "#1a1a2e",  # footer text color
            "status": 1,  # active
            }
            ]

        for theme_data in themes_data:
            theme, created = Themes.objects.update_or_create(
                name=theme_data['name'],
                defaults=theme_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Theme '{theme.name}' created successfully."))
            else:
                self.stdout.write(self.style.WARNING(f"Theme '{theme.name}' already exists, updated with new values."))


