from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from accounts.models import User
from location.models import Country
from django.utils.text import slugify

class Command(BaseCommand):
    help = "Create country list"

    def handle(self, *args, **kwargs):
        #Country.objects.get(name='china').delete()
        for country in Country.objects.all():
            print(country)
            if not country.slug:
                base_slug = slugify(country.name)
                slug = base_slug
                num = 1
                while Country.objects.filter(slug=slug).exclude(id=country.id).exists():
                    slug = f"{base_slug}-{num}"
                    num += 1
                country.slug = slug
                country.save()
