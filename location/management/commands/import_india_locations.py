import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.text import slugify
from django.core.exceptions import ValidationError
import random

from location.models import Country, Location, SubLocation

STATUS_CHOICES = [1, -1, 0]

class Command(BaseCommand):
    help = "Import India locations: State → Location, City → SubLocation (handle duplicates)"

    def handle(self, *args, **kwargs):
        base_dir = Path(settings.BASE_DIR) / "ims" / "static" / "data"

        countries_file = base_dir / "countries.json"
        states_file = base_dir / "states.json"
        cities_file = base_dir / "cities.json"

        country_map = self.import_countries(countries_file)
        state_map = self.import_states(states_file, country_map)
        self.import_cities(cities_file, state_map)

        self.stdout.write(self.style.SUCCESS("✅ Import completed successfully"))

    # ===================== COUNTRY =====================
    def import_countries(self, file_path):
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        country_map = {}

        for c in data:
            if c.get("iso2", "").upper() != "IN":
                continue

            country, created = Country.objects.get_or_create(
                code="IN",
                defaults={
                    "name": c["name"],
                    "slug": slugify(c["name"]),
                    "status": 1
                },
            )

            country_map[c["id"]] = country
            self.stdout.write(f"{'Created' if created else 'Skipped'} country: {country.name}")

        return country_map

    # ===================== STATE → LOCATION =====================
    def import_states(self, file_path, country_map):
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        state_map = {}

        for s in data:
            country = country_map.get(s["country_id"])
            if not country:
                continue

            location, created = Location.objects.get_or_create(
                name=s["name"],
                country=country,
                city=None,
                defaults={
                    "region": s["name"],
                    "slug": self.unique_slug(Location, s["name"]),
                    "code": self.unique_code(Location, s["name"], 4),
                    "status": random.choice(STATUS_CHOICES),
                },
            )

            state_map[s["id"]] = location
            self.stdout.write(f"{'Created' if created else 'Skipped'} state: {location.name}")

        return state_map

    # ===================== CITY → SUBLOCATION =====================
    def import_cities(self, file_path, state_map):
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        for c in data:
            state = state_map.get(c["state_id"])
            if not state:
                continue

            city_name = c["name"]

            # 1️⃣ Same city + same state → skip
            if SubLocation.objects.filter(name=city_name, location=state).exists():
                self.stdout.write(f"Skipped city (same state): {city_name}")
                continue

            final_name = city_name

            # 2️⃣ City exists but in different state → rename
            if SubLocation.objects.filter(name=city_name).exists():
                final_name = f"{state.name}_{city_name}"

            try:
                SubLocation.objects.create(
                    name=final_name,
                    location=state,
                    slug=self.unique_slug(SubLocation, final_name),
                    code=self.unique_code(SubLocation, final_name, 6),
                    status=random.choice(STATUS_CHOICES),
                )
                self.stdout.write(f"Created city: {final_name}")

            except ValidationError:
                self.stdout.write(f"Skipped city (validation): {final_name}")

    # ===================== HELPERS =====================
    def unique_slug(self, model, base):
        slug = slugify(base)
        new_slug = slug
        i = 1
        while model.objects.filter(slug=new_slug).exists():
            new_slug = f"{slug}-{i}"
            i += 1
        return new_slug

    def unique_code(self, model, base, length):
        code = slugify(base)[:length].upper()
        new_code = code
        i = 1
        while model.objects.filter(code=new_code).exists():
            new_code = f"{code}{i}"
            i += 1
        return new_code
