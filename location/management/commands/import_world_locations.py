import os
import json
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from location.models import Country, Location


class Command(BaseCommand):
    help = 'Import world countries, states, and cities safely (rerunnable)'

    def handle(self, *args, **kwargs):
        base_dir = os.path.join(os.path.dirname(__file__), '../../../ims/static/data')
        countries_file = os.path.join(base_dir, 'countries.json')
        states_file = os.path.join(base_dir, 'states.json')
        cities_file = os.path.join(base_dir, 'cities.json')

        # ===================== COUNTRIES =====================
        with open(countries_file, 'r', encoding='utf-8') as f:
            countries_data = json.load(f)

        country_map = {}
        for c in countries_data:
            code = (c.get('iso2') or '').upper()
            country = Country.objects.filter(code=code).first()

            if country:
                self.stdout.write(f"Skipping existing country: {country.name}")
            else:
                name = c['name']
                slug = self.unique_slug(Country, name)
                country = Country.objects.create(
                    name=name,
                    code=code,
                    slug=slug
                )
                self.stdout.write(f"Created country: {country.name}")

            country_map[c['id']] = country

        # ===================== STATES / REGIONS =====================
        with open(states_file, 'r', encoding='utf-8') as f:
            states_data = json.load(f)

        state_map = {}
        for s in states_data:
            country = country_map.get(s['country_id'])
            if not country:
                continue

            existing = Location.objects.filter(
                name=s['name'],
                country=country,
                region=s['name']
            ).first()

            if existing:
                self.stdout.write(f"Skipping existing state/region: {existing.name}")
                state_map[s['id']] = existing
                continue

            state = self.safe_create_location(
                name=s['name'],
                country=country,
                region=s['name'],
                slug=self.unique_slug(Location, s['name']),
                code=self.unique_code(Location, s['name'], 4)
            )

            state_map[s['id']] = state
            self.stdout.write(f"Created state/region: {state.name}")

        # ===================== CITIES =====================
        with open(cities_file, 'r', encoding='utf-8') as f:
            cities_data = json.load(f)

        for c in cities_data:
            country = country_map.get(c['country_id'])
            state = state_map.get(c['state_id'])
            if not country or not state:
                continue

            self.safe_create_location(
                name=c['name'],
                country=country,
                region=state.region,
                city=c['name'],
                slug=self.unique_slug(Location, c['name']),
                code=self.unique_code(Location, c['name'], 6)
            )

            self.stdout.write(f"Created city: {c['name']}")

        self.stdout.write(self.style.SUCCESS("✅ Import completed successfully"))

    # ===================== SAFE CREATION =====================

    def safe_create_location(self, **kwargs):
        """
        Safely create Location even if name/slug/code are unique.
        Automatically appends numbers if needed.
        """
        base_name = kwargs['name']
        base_slug = kwargs['slug']
        base_code = kwargs['code']
        i = 1

        while True:
            try:
                return Location.objects.create(**kwargs)
            except ValidationError:
                kwargs['name'] = f"{base_name} {i}"
                kwargs['slug'] = f"{base_slug}-{i}"
                kwargs['code'] = f"{base_code}{i}"
                i += 1

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
