from django.core.management.base import BaseCommand
from catalog.models import (
    Manufacturer, Languages, Brand, ProductType, Category, Product, ProductLinks, ProductGroup, Languages
)
import random
from location.models import Country
from datetime import datetime
from accounts.models import User
import traceback
class Command(BaseCommand):
    help = "Insert master data and test products using update_or_create"

    def random_product_attr_data(self):
        # Dimensions
        length = round(random.uniform(5, 200), 2)  # cm
        width = round(random.uniform(5, 200), 2)   # cm
        height = round(random.uniform(5, 200), 2)  # cm
        dimensions = f"{length} x {width} x {height} cm"

        # Weight (Net/Gross)
        net_weight = round(random.uniform(0.1, 50), 2)  # kg
        gross_weight = round(net_weight + random.uniform(0.1, 5), 2)
        weight = f"{net_weight} kg / {gross_weight} kg"

        # Materials
        materials_list = ["Plastic", "Steel", "Aluminum", "Wood", "Glass", "Cotton", "Leather"]
        materials = ", ".join(random.sample(materials_list, random.randint(1, 3)))

        # Packaging
        packaging_types = ["Box", "Pallet", "Bag", "Crate", "Envelope", "Tube"]
        packaging = random.choice(packaging_types)

        # Warranty
        warranty_options = ["No Warranty", "6 Months", "1 Year", "2 Years", "5 Years"]
        warranty = random.choice(warranty_options)

        return_policies = [
            "No Returns Accepted",
            "7 Days Return",
            "14 Days Return",
            "30 Days Return",
            "Exchange Only",
        ]
        return_policy = random.choice(return_policies)

        return {
            "attribute_1": dimensions,
            "attribute_2": weight,
            "attribute_3": materials,
            "attribute_4": packaging,
            "attribute_5": warranty,
            "attribute_6" : return_policy
        }

    def handle(self, *args, **kwargs):
        created_user =  User.objects.filter(pk=2).first()
        updated_user =  User.objects.filter(pk=1).first()
        # Master data
        categories = [
            "TV", "Washing Machine", "Refrigerator", "Oven", "Laptop", "Dishwasher", "Mobile"
        ]

        product_types = ["FERT(Finished Goods)", "HAWA(Trading Goods)", "ROH(Raw Material)", "HALB(Semi-finished)", "DIEN(Services)"]

        product_groups = [
                "Electronics", "Chemicals", "Fabric Rolls", "office services"
            ]


        manufacturers = ["Dairy Farmers of America", "Nestle", "Hero", "Hyundai", "Tata", 'Others']

        brands = ['Apple', "Microsoft", "Amazon", "HP", "Samsung", "Sony", "Others"]

        countries = [
            {'name': 'India', 'code': 'IN'},
            {'name': 'USA', 'code': 'US'},
            {'name': 'Germany', 'code': 'DE'},
            {'name': 'Japan', 'code': 'JP'},
            {'name': 'China', 'code': 'CN'}
        ]

        languages = [
            {'name': "English", "code": "en"},
            {'name': "Hindi", "code": "hi"},
            {'name': "German", "code": "de"},
            {'name': "Japanese", "code": "jp"}
        ]

        PRODUCT_NAMES = [
            # Performance / Premium
                "Pro Max", "Ultra", "Elite", "Prime", "X", "S", "Plus", "Neo", "Edge", "One", "Core", "Power",

                # Compact / Lightweight
                "Mini", "Lite", "Go", "Air", "Flex",

                # Smart / Modern
                "Vision", "Smart", "IQ", "Next", "Connect", "Live",

                # Tech / Innovation
                "Infinity", "Fusion", "Volt", "Pulse", "Nova", "Zen", "Element"
            ]
        # Insert Categories
        for i, name in enumerate(categories, start=1):
            Category.objects.update_or_create(
                name=name,
                created_user=created_user,
                updated_user=updated_user,
                defaults={
                    'status': 1,
                    'code': f"PC-{name.upper()[:2]}-{i}"
                }
            )

        # Insert Product Types
        for i, name in enumerate(product_types, start=1):
            ProductType.objects.update_or_create(
                name=name,
                created_user=created_user,
                updated_user=updated_user,
                defaults={
                    'status': 1,
                    'code': f"PT-{name.upper()[:2]}-{i}"
                }
            )

        # # Insert Product Groups
        for i, item in enumerate(product_groups, start=1):
            ProductGroup.objects.update_or_create(
                name=item,
                created_user=created_user,
                updated_user=updated_user,
                defaults={
                    'status': 1,
                    'code': f"PG-{item.upper()[:2]}-{i}"
                }
            )

        # Insert Manufacturers
        for i, name in enumerate(manufacturers, start=1):
            Manufacturer.objects.update_or_create(
                name=name,
                created_user=created_user,
                updated_user=updated_user,
                defaults={
                    'status': 1,
                    'code': f"PM-{name.upper()[:2]}-{i}"
                }
            )

        # Insert Brands
        for i, name in enumerate(brands, start=1):
            Brand.objects.update_or_create(
                name=name,
                created_user=created_user,
                updated_user=updated_user,
                defaults={
                    'status': 1,
                    'code': f"PB-{name.upper()[:2]}-{i}"
                }
            )

        # Insert Countries
        for i, item in enumerate(countries, start=1):
            Country.objects.update_or_create(
                name=item['name'],
                created_user=created_user,
                updated_user=updated_user,
                defaults={
                    'status': 1,
                    'code': f"AC-{item['name'].upper()[:2]}-{i}"
                }
            )

        # Insert Languages
        for i, item in enumerate(languages, start=1):
            Languages.objects.update_or_create(  # assuming model is singular
                name=item['name'],
                created_user=created_user,
                updated_user=updated_user,
                defaults={
                    'status': 1,
                    'code': f"AL-{item['name'].upper()[:2]}-{i}"
                }
            )




        # # Helper to get foreign keys
        def get_fk(model, name):
            try:
                return model.objects.get(name=name)
            except model.DoesNotExist:
                return None

        categories = list(Category.objects.all())
        product_types = list(ProductType.objects.all())
        brands = list(Brand.objects.all())
        manufacturers = list(Manufacturer.objects.all())
        languages = list(Languages.objects.all())
        countries = list(Country.objects.all())
        product_group =  list(ProductGroup.objects.all())

        for i in range(1, 51):
            category = random.choice(categories)
            product_type = random.choice(product_types)
            brand = random.choice(brands)
            manufacturer = random.choice(manufacturers)
            language = random.choice(languages)
            country = random.choice(countries)
            pgroup = random.choice(product_group)

            name = f"{brand.name} {random.choice(PRODUCT_NAMES)} {i}"

            #attr_data = self.random_product_attr_data()
            try:
                pdata = {
                        'category': category,
                        'product_type': product_type,
                        'brand': brand,
                        'manufacturer': manufacturer,
                        'language': language,
                        'country': country,
                        'product_group' : pgroup,
                        'long_description': f"Long description for {name}",
                        'short_description': f"Short description for {name}",
                        'unit_of_measure': 'pcs',
                        'mpin': f"{1000+i}",
                        'upc': f"{2000+i:04d}",
                        'isbn': f"ISBN-{300000+i}",
                        'ean': f"{4000000000000+i}",
                        'status': 1,
                        'created_user_id' : 2,
                        'updated_user_id' : 1,
                    }
                #pdata.update(attr_data)
                

                product, created = Product.objects.update_or_create(
                    name=name,
                    created_user=created_user,
                    updated_user=updated_user,
                    code=f"PI-{name.upper():3}-{i}",
                    defaults=pdata
                )

                # Add 2 product links
                for j in range(2):
                    ProductLinks.objects.update_or_create(
                        product=product,
                        created_user=created_user,
                        updated_user=updated_user,
                        url=f"https://amazon.com/{name.replace(' ','_')}/link{j+1}"
                    )
            except Exception as e:
                traceback.print_exc()
                print (e)


        self.stdout.write(self.style.SUCCESS("Master data and test products setup complete!"))
