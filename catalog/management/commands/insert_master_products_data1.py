import random
import re
import requests

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile

from catalog.models import Product
from ims.models import Units, ProcurementType


PRODUCTS = [
{"name":"Samsung Galaxy S21","short_desc":"Galaxy S21 Smartphone","long_desc":"Samsung Galaxy S21 smartphone with AMOLED display and 128GB storage.","unit":"pcs","image":"https://source.unsplash.com/600x600/?samsung-phone"},
{"name":"Apple iPhone 13","short_desc":"iPhone 13 Smartphone","long_desc":"Apple iPhone 13 powered by A15 Bionic chip.","unit":"pcs","image":"https://source.unsplash.com/600x600/?iphone"},
{"name":"Sony PlayStation 5","short_desc":"PS5 Console","long_desc":"Sony PlayStation 5 next generation gaming console.","unit":"pcs","image":"https://source.unsplash.com/600x600/?playstation"},
{"name":"Apple MacBook Pro","short_desc":"MacBook Laptop","long_desc":"Apple MacBook Pro laptop with M2 processor.","unit":"pcs","image":"https://source.unsplash.com/600x600/?macbook"},
{"name":"Dell XPS 13","short_desc":"XPS Laptop","long_desc":"Dell XPS 13 ultrabook laptop.","unit":"pcs","image":"https://source.unsplash.com/600x600/?laptop"},
{"name":"HP LaserJet Printer","short_desc":"Laser Printer","long_desc":"HP LaserJet high speed office printer.","unit":"pcs","image":"https://source.unsplash.com/600x600/?printer"},
{"name":"Logitech Wireless Mouse","short_desc":"Wireless Mouse","long_desc":"Logitech ergonomic wireless mouse.","unit":"pcs","image":"https://source.unsplash.com/600x600/?computer-mouse"},
{"name":"Logitech Mechanical Keyboard","short_desc":"Mechanical Keyboard","long_desc":"Logitech RGB mechanical gaming keyboard.","unit":"pcs","image":"https://source.unsplash.com/600x600/?keyboard"},
{"name":"Canon EOS 90D","short_desc":"Canon DSLR Camera","long_desc":"Canon EOS 90D DSLR professional camera.","unit":"pcs","image":"https://source.unsplash.com/600x600/?dslr-camera"},
{"name":"Nikon D7500","short_desc":"Nikon DSLR","long_desc":"Nikon D7500 professional photography camera.","unit":"pcs","image":"https://source.unsplash.com/600x600/?nikon-camera"},
{"name":"Bose QuietComfort Headphones","short_desc":"Noise Cancelling Headphones","long_desc":"Bose premium noise cancelling headphones.","unit":"pcs","image":"https://source.unsplash.com/600x600/?headphones"},
{"name":"Sony WH-1000XM5","short_desc":"Sony Wireless Headphones","long_desc":"Sony WH1000XM5 wireless noise cancelling headphones.","unit":"pcs","image":"https://source.unsplash.com/600x600/?sony-headphones"},
{"name":"JBL Flip 6","short_desc":"Bluetooth Speaker","long_desc":"JBL Flip portable waterproof bluetooth speaker.","unit":"pcs","image":"https://source.unsplash.com/600x600/?bluetooth-speaker"},
{"name":"Apple Watch Series 8","short_desc":"Smart Watch","long_desc":"Apple Watch Series 8 smartwatch with health tracking.","unit":"pcs","image":"https://source.unsplash.com/600x600/?smartwatch"},
{"name":"Samsung Galaxy Watch","short_desc":"Samsung Smartwatch","long_desc":"Samsung Galaxy smartwatch with fitness tracking.","unit":"pcs","image":"https://source.unsplash.com/600x600/?samsung-watch"},
{"name":"Nike Air Max","short_desc":"Running Shoes","long_desc":"Nike Air Max comfortable running shoes.","unit":"pair","image":"https://source.unsplash.com/600x600/?running-shoes"},
{"name":"Adidas Ultraboost","short_desc":"Adidas Running Shoes","long_desc":"Adidas Ultraboost premium running shoes.","unit":"pair","image":"https://source.unsplash.com/600x600/?adidas-shoes"},
{"name":"Puma Sports Shoes","short_desc":"Puma Shoes","long_desc":"Puma lightweight sports shoes.","unit":"pair","image":"https://source.unsplash.com/600x600/?sports-shoes"},
{"name":"Lenovo ThinkPad X1","short_desc":"Business Laptop","long_desc":"Lenovo ThinkPad X1 Carbon business laptop.","unit":"pcs","image":"https://source.unsplash.com/600x600/?thinkpad"},
{"name":"Asus ROG Laptop","short_desc":"Gaming Laptop","long_desc":"Asus ROG gaming laptop with RTX GPU.","unit":"pcs","image":"https://source.unsplash.com/600x600/?gaming-laptop"},
{"name":"Acer Predator Monitor","short_desc":"Gaming Monitor","long_desc":"Acer Predator 27 inch gaming monitor.","unit":"pcs","image":"https://source.unsplash.com/600x600/?gaming-monitor"},
{"name":"Samsung 4K Smart TV","short_desc":"4K Television","long_desc":"Samsung 55 inch 4K UHD smart television.","unit":"pcs","image":"https://source.unsplash.com/600x600/?smart-tv"},
{"name":"LG OLED TV","short_desc":"OLED Television","long_desc":"LG OLED 65 inch smart television.","unit":"pcs","image":"https://source.unsplash.com/600x600/?oled-tv"},
{"name":"Mi Smart TV","short_desc":"Android TV","long_desc":"Mi Android smart TV with Dolby Vision.","unit":"pcs","image":"https://source.unsplash.com/600x600/?android-tv"},
{"name":"Philips Air Fryer","short_desc":"Kitchen Air Fryer","long_desc":"Philips healthy air fryer for oil-free cooking.","unit":"pcs","image":"https://source.unsplash.com/600x600/?air-fryer"},
{"name":"Instant Pot Cooker","short_desc":"Electric Pressure Cooker","long_desc":"Instant pot multi-functional pressure cooker.","unit":"pcs","image":"https://source.unsplash.com/600x600/?pressure-cooker"},
{"name":"KitchenAid Mixer","short_desc":"Kitchen Mixer","long_desc":"KitchenAid professional stand mixer.","unit":"pcs","image":"https://source.unsplash.com/600x600/?kitchen-mixer"},
{"name":"Dyson Vacuum Cleaner","short_desc":"Vacuum Cleaner","long_desc":"Dyson cordless vacuum cleaner.","unit":"pcs","image":"https://source.unsplash.com/600x600/?vacuum-cleaner"},
{"name":"Roomba Robot Vacuum","short_desc":"Robot Cleaner","long_desc":"Roomba smart robot vacuum cleaner.","unit":"pcs","image":"https://source.unsplash.com/600x600/?robot-vacuum"},
{"name":"Google Nest Hub","short_desc":"Smart Display","long_desc":"Google Nest Hub smart home display.","unit":"pcs","image":"https://source.unsplash.com/600x600/?smart-home"},
]


NUM_PRODUCTS = 100
COUNTRY_ID = 1


def slugify_text(text):
    text = text.lower()
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'[^a-z0-9_-]', '', text)
    return text


class Command(BaseCommand):
    help = "Insert 100 realistic products with images"

    def handle(self, *args, **kwargs):

        units_cache = {u.unit: u for u in Units.objects.all()}
        procurement_types = list(ProcurementType.objects.all())

        for i in range(1, NUM_PRODUCTS + 1):

            base = random.choice(PRODUCTS)

            name = f"{base['name']}_{i}"
            slug = slugify_text(name)
            code = f"PRD{i:05d}"

            unit_name = base["unit"]

            if unit_name not in units_cache:
                units_cache[unit_name] = Units.objects.create(unit=unit_name)

            unit_obj = units_cache[unit_name]

            procurement = random.choice(procurement_types)

            product, created = Product.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "slug": slug,
                    "status": 1,

                    "category_id": random.randint(1, 10),
                    "product_type_id": random.randint(1, 10),
                    "product_group_id": random.randint(1, 10),
                    "brand_id": random.randint(1, 10),
                    "manufacturer_id": random.randint(1, 10),
                    "language_id": random.randint(1, 5),
                    "country_id": COUNTRY_ID,

                    "long_description": base["long_desc"],
                    "short_description": base["short_desc"],

                    "unit_of_measure": unit_obj,
                    "procurementtype": procurement,

                    "mpin": str(random.randint(1000, 9999)),
                    "upc": str(random.randint(1000, 9999)),
                    "isbn": str(random.randint(1000000000000, 9999999999999)),
                    "ean": str(random.randint(1000000000000, 9999999999999)),

                    "notes": f"Notes for {name}",
                    "serialnumber_status": random.choice([0, 1]),
                    "prefix": f"SN{i:04d}",
                    "specification": f"Specification for {name}",
                    "model_number": f"MDL-{i:04d}",
                    "source_of_make": random.choice(["India","USA","Germany","China"]),
                    "material_code": f"MAT-{i:04d}",
                }
            )

            # Download and save image
            if created and base.get("image"):
                try:
                    response = requests.get(base["image"], timeout=5)

                    if response.status_code == 200:
                        product.image.save(
                            f"{slug}.jpg",
                            ContentFile(response.content),
                            save=True
                        )
                except Exception as e:
                    self.stdout.write(f"Image download failed for {name}")

        self.stdout.write(self.style.SUCCESS("✅ 100 Products inserted successfully"))