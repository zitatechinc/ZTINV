from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from accounts.models import User
from location.models import Country, Location, SubLocation
from django.utils.text import slugify
class Command(BaseCommand):
    help = "Create default users for each group with password rm#123"

    

    def handle(self, *args, **kwargs):

        # Step 1: Create 10 Locations
        # Location.objects.all().delete()
        user_obj = User.objects.filter(pk=1).first()
        locations = []
        country_cls = Country.objects.filter(name__icontains='india').first()
        for i in range(1, 50):   # PL01 to PL10
            locations.append(Location(code=f"PL{i:02d}", name=f"Plant {i}", country=country_cls, created_user=user_obj, region='Telangana'))
        Location.objects.bulk_create(locations)

        # Step 2: Reload saved locations (since bulk_create doesn’t return PKs)
        locations = list(Location.objects.all())
        sublocations = list(SubLocation.objects.all())
        print (locations)
        print (sublocations)

        # # Step 3: Create 100+ SubLocations
        sublocations = []
        for loc in locations:
            for j in range(1, 25):   # Each location has 10 SubLocations
                sublocations.append(SubLocation(
                    location=loc,
                    code=f"S{j:02d}-PL{loc.code}",               # S01, S02...
                    name=f"SubLocation {j} of {loc.code}",
                    created_user=user_obj
                ))

        SubLocation.objects.bulk_create(sublocations)

        print("✅ Inserted", len(locations), "Locations and", len(sublocations), "SubLocations")

        pass
       