from .models import AppSettings
from django.conf import settings

def app_custom_processor(request):
    app = AppSettings.objects.all().first()
    if app and app.theme and app.theme.status in (-1, 0):
        app.theme_id=settings.DEFAULT_THEME
        app.save()
    if app:
        return {
            'app': app
        }
    else:
        return {

        'app' : {
        'logo' :  '/logo.png',
        'favicon' : "/favicon.jpg",
        "name" : "Inventory App",
        "company_name" : "ZitaTech Pvt Ltd",
        "header_text" : "AI Smart Inventory App",
        "footer_text" : "ZitaTech Pvt Ltd"

        }
        }
