import random
import re
from django.core.management.base import BaseCommand
from catalog.models import Product, Brand, Category, ProductGroup, ProductType, Manufacturer, Languages, Country
from ims.models import Units, ProcurementType

# Number of products to generate
NUM_PRODUCTS = 5

# Sample products
PRODUCTS = [
    {"name": "Galaxy S21", "brand": "Samsung", "long_desc": "Samsung Galaxy S21 smartphone with 128GB storage and 8GB RAM.", "short_desc": "Galaxy S21"},
    {"name": "iPhone 13", "brand": "Apple", "long_desc": "Apple iPhone 13 with A15 Bionic chip and 128GB storage.", "short_desc": "iPhone 13"},
    {"name": "PlayStation 5", "brand": "Sony", "long_desc": "Sony PlayStation 5 gaming console with Ultra HD graphics.", "short_desc": "PS5"},
    {"name": "Xbox Series X", "brand": "Microsoft", "long_desc": "Microsoft Xbox Series X with 1TB SSD and high-end GPU.", "short_desc": "Xbox Series X"},
]


def make_slug(text):
    text = text.lower()
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'[^a-z0-9_-]', '', text)
    return text


class Command(BaseCommand):
    help = "Seed sample products"

    def handle(self, *args, **kwargs):

        # Load ORM objects once (faster)
        brands = list(Brand.objects.all())
        categories = list(Category.objects.all())
        product_groups = list(ProductGroup.objects.all())
        product_types = list(ProductType.objects.all())
        manufacturers = list(Manufacturer.objects.all())
        languages = list(Languages.objects.all())
        countries = list(Country.objects.all())
        units = list(Units.objects.all())
        procurements = list(ProcurementType.objects.all())

        for i in range(1, NUM_PRODUCTS + 1):

            base = random.choice(PRODUCTS)

            name = f"{base['name']} {i}"
            slug = make_slug(name)
            code = f"PRD{i:04d}"

            brand = random.choice(brands)
            category = random.choice(categories)
            product_group = random.choice(product_groups)
            product_type = random.choice(product_types)
            manufacturer = random.choice(manufacturers)
            language = random.choice(languages)
            country = random.choice(countries)
            unit = random.choice(units)
            procurement = random.choice(procurements)

            mpin = str(random.randint(1000, 9999))
            upc = str(random.randint(1000, 9999))
            isbn = str(random.randint(1000000000000, 9999999999999))
            ean = str(random.randint(1000000000000, 9999999999999))

            Product.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "slug": slug,
                    "status": 1,

                    "category": category,
                    "product_type": product_type,
                    "product_group": product_group,
                    "brand": brand,
                    "manufacturer": manufacturer,
                    "language": language,
                    "country": country,

                    "long_description": base["long_desc"],
                    "short_description": base["short_desc"],

                    "unit_of_measure": unit,
                    "procurementtype": procurement,

                    "specification": f"{name} specification",
                    "model_number": f"MDL-{i}",
                    "source_of_make": "India",

                    "serialnumber_status": 0,
                    "prefix": f"SN{i}",
                    "material_code": f"MAT{i:04d}",

                    "mpin": mpin,
                    "upc": upc,
                    "isbn": isbn,
                    "ean": ean,

                    "notes": f"Notes for {name}",

                    "image": None,
                    "file": None,
                }
            )

        self.stdout.write(self.style.SUCCESS(f"{NUM_PRODUCTS} products inserted successfully"))