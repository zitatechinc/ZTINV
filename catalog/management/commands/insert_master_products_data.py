import random
from django.core.management.base import BaseCommand
from catalog.models import Product

# Sample realistic data
PRODUCTS = [
    {"name": "Galaxy S21", "brand": "Samsung", "long_desc": "Samsung Galaxy S21 smartphone with 128GB storage and 8GB RAM.", "short_desc": "Galaxy S21", "unit": "pcs"},
    {"name": "iPhone 13", "brand": "Apple", "long_desc": "Apple iPhone 13 with A15 Bionic chip and 128GB storage.", "short_desc": "iPhone 13", "unit": "pcs"},
    {"name": "PlayStation 5", "brand": "Sony", "long_desc": "Sony PlayStation 5 gaming console with Ultra HD graphics.", "short_desc": "PS5", "unit": "unit"},
    {"name": "Xbox Series X", "brand": "Microsoft", "long_desc": "Microsoft Xbox Series X with 1TB SSD and high-end GPU.", "short_desc": "Xbox Series X", "unit": "unit"},
    {"name": "MacBook Pro 14", "brand": "Apple", "long_desc": "Apple MacBook Pro 14-inch laptop with M1 Pro chip, 16GB RAM.", "short_desc": "MacBook Pro 14", "unit": "pcs"},
    {"name": "Dell XPS 13", "brand": "Dell", "long_desc": "Dell XPS 13 ultrabook with Intel i7, 16GB RAM, 512GB SSD.", "short_desc": "Dell XPS 13", "unit": "pcs"},
    {"name": "HP Spectre x360", "brand": "HP", "long_desc": "HP Spectre x360 convertible laptop with 13.3-inch FHD touchscreen.", "short_desc": "HP Spectre x360", "unit": "pcs"},
    {"name": "Lenovo ThinkPad X1", "brand": "Lenovo", "long_desc": "Lenovo ThinkPad X1 Carbon business laptop, durable and powerful.", "short_desc": "ThinkPad X1", "unit": "pcs"},
    {"name": "Sony WH-1000XM4", "brand": "Sony", "long_desc": "Sony WH-1000XM4 wireless noise-cancelling headphones.", "short_desc": "Sony WH-1000XM4", "unit": "pcs"},
    {"name": "Bose QuietComfort 35", "brand": "Bose", "long_desc": "Bose QC35 wireless noise-cancelling headphones with 20h battery.", "short_desc": "Bose QC35", "unit": "pcs"},
    {"name": "Canon EOS R5", "brand": "Canon", "long_desc": "Canon EOS R5 mirrorless camera with 45MP sensor.", "short_desc": "Canon EOS R5", "unit": "pcs"},
    {"name": "Nikon Z7 II", "brand": "Nikon", "long_desc": "Nikon Z7 II mirrorless camera with 45.7MP sensor.", "short_desc": "Nikon Z7 II", "unit": "pcs"},
    {"name": "iPad Pro 12.9", "brand": "Apple", "long_desc": "Apple iPad Pro 12.9-inch with M1 chip and 128GB storage.", "short_desc": "iPad Pro 12.9", "unit": "pcs"},
    {"name": "Galaxy Tab S7", "brand": "Samsung", "long_desc": "Samsung Galaxy Tab S7 with 11-inch display and S Pen.", "short_desc": "Galaxy Tab S7", "unit": "pcs"},
    {"name": "AirPods Pro", "brand": "Apple", "long_desc": "Apple AirPods Pro with active noise cancellation.", "short_desc": "AirPods Pro", "unit": "pcs"},
    {"name": "JBL Flip 5", "brand": "JBL", "long_desc": "JBL Flip 5 portable Bluetooth speaker, waterproof.", "short_desc": "JBL Flip 5", "unit": "pcs"},
    {"name": "Sony Alpha a7 III", "brand": "Sony", "long_desc": "Sony Alpha a7 III full-frame mirrorless camera.", "short_desc": "Sony a7 III", "unit": "pcs"},
    {"name": "Fujifilm X-T4", "brand": "Fujifilm", "long_desc": "Fujifilm X-T4 mirrorless camera with 26.1MP sensor.", "short_desc": "Fujifilm X-T4", "unit": "pcs"},
    {"name": "Dyson V11 Vacuum", "brand": "Dyson", "long_desc": "Dyson V11 cordless vacuum cleaner with high suction.", "short_desc": "Dyson V11", "unit": "pcs"},
    {"name": "KitchenAid Mixer", "brand": "KitchenAid", "long_desc": "KitchenAid stand mixer with 5-quart bowl.", "short_desc": "KitchenAid Mixer", "unit": "pcs"},
    {"name": "Nike Air Max", "brand": "Nike", "long_desc": "Nike Air Max running shoes with cushioned sole.", "short_desc": "Nike Air Max", "unit": "pair"},
    {"name": "Adidas Ultraboost", "brand": "Adidas", "long_desc": "Adidas Ultraboost running shoes, responsive cushioning.", "short_desc": "Adidas Ultraboost", "unit": "pair"},
    {"name": "Puma Suede Classic", "brand": "Puma", "long_desc": "Puma Suede Classic sneakers, stylish casual wear.", "short_desc": "Puma Suede Classic", "unit": "pair"},
    {"name": "Rolex Submariner", "brand": "Rolex", "long_desc": "Rolex Submariner luxury dive watch.", "short_desc": "Rolex Submariner", "unit": "pcs"},
    {"name": "Casio G-Shock", "brand": "Casio", "long_desc": "Casio G-Shock shock-resistant digital watch.", "short_desc": "Casio G-Shock", "unit": "pcs"},
    {"name": "Timex Weekender", "brand": "Timex", "long_desc": "Timex Weekender casual analog watch.", "short_desc": "Timex Weekender", "unit": "pcs"},
    {"name": "Ikea Billy Bookcase", "brand": "Ikea", "long_desc": "Ikea Billy bookcase with adjustable shelves.", "short_desc": "Billy Bookcase", "unit": "pcs"},
    {"name": "Home Depot Drill", "brand": "Home Depot", "long_desc": "Cordless drill with battery pack and charger.", "short_desc": "Cordless Drill", "unit": "pcs"},
    {"name": "Bosch Hammer Drill", "brand": "Bosch", "long_desc": "Bosch hammer drill with high torque.", "short_desc": "Bosch Drill", "unit": "pcs"},
    {"name": "Makita Cordless Drill", "brand": "Makita", "long_desc": "Makita cordless drill with long battery life.", "short_desc": "Makita Drill", "unit": "pcs"},
    {"name": "Canon Pixma Printer", "brand": "Canon", "long_desc": "Canon Pixma inkjet printer with wireless connectivity.", "short_desc": "Canon Pixma Printer", "unit": "pcs"},
    {"name": "HP LaserJet Printer", "brand": "HP", "long_desc": "HP LaserJet printer for home and office.", "short_desc": "HP LaserJet", "unit": "pcs"},
    {"name": "Dell UltraSharp Monitor", "brand": "Dell", "long_desc": "Dell UltraSharp 27-inch 4K monitor.", "short_desc": "Dell Monitor", "unit": "pcs"},
    {"name": "LG UltraGear Monitor", "brand": "LG", "long_desc": "LG UltraGear 32-inch gaming monitor, 144Hz.", "short_desc": "LG UltraGear", "unit": "pcs"},
    {"name": "Apple Watch Series 6", "brand": "Apple", "long_desc": "Apple Watch Series 6 with ECG and blood oxygen.", "short_desc": "Apple Watch 6", "unit": "pcs"},
    {"name": "Samsung Galaxy Watch 3", "brand": "Samsung", "long_desc": "Samsung Galaxy Watch 3 with health tracking features.", "short_desc": "Galaxy Watch 3", "unit": "pcs"},
    {"name": "OnePlus 9", "brand": "OnePlus", "long_desc": "OnePlus 9 smartphone with Snapdragon 888.", "short_desc": "OnePlus 9", "unit": "pcs"},
    {"name": "Huawei P40", "brand": "Huawei", "long_desc": "Huawei P40 smartphone with Leica camera system.", "short_desc": "Huawei P40", "unit": "pcs"},
    {"name": "Xiaomi Mi 11", "brand": "Xiaomi", "long_desc": "Xiaomi Mi 11 with 108MP camera and 120Hz display.", "short_desc": "Xiaomi Mi 11", "unit": "pcs"},
    {"name": "Oppo Find X3", "brand": "Oppo", "long_desc": "Oppo Find X3 smartphone with AMOLED display.", "short_desc": "Oppo Find X3", "unit": "pcs"},
    {"name": "Vivo X60", "brand": "Vivo", "long_desc": "Vivo X60 with gimbal camera stabilization.", "short_desc": "Vivo X60", "unit": "pcs"},
    {"name": "Motorola Edge", "brand": "Motorola", "long_desc": "Motorola Edge smartphone with curved display.", "short_desc": "Motorola Edge", "unit": "pcs"},
    {"name": "Galaxy Buds Pro", "brand": "Samsung", "long_desc": "Samsung Galaxy Buds Pro true wireless earbuds.", "short_desc": "Galaxy Buds Pro", "unit": "pcs"},
    {"name": "Apple AirPods Max", "brand": "Apple", "long_desc": "Apple AirPods Max over-ear headphones with spatial audio.", "short_desc": "AirPods Max", "unit": "pcs"},
    {"name": "Sony WF-1000XM4", "brand": "Sony", "long_desc": "Sony WF-1000XM4 in-ear noise-cancelling headphones.", "short_desc": "Sony WF-1000XM4", "unit": "pcs"},
    {"name": "JBL Charge 5", "brand": "JBL", "long_desc": "JBL Charge 5 portable Bluetooth speaker, waterproof.", "short_desc": "JBL Charge 5", "unit": "pcs"},
    {"name": "Canon EOS R6", "brand": "Canon", "long_desc": "Canon EOS R6 mirrorless camera with 20MP sensor.", "short_desc": "Canon EOS R6", "unit": "pcs"},
    {"name": "Nikon D850", "brand": "Nikon", "long_desc": "Nikon D850 DSLR camera with 45.7MP full-frame sensor.", "short_desc": "Nikon D850", "unit": "pcs"},
    {"name": "Samsung QLED TV", "brand": "Samsung", "long_desc": "Samsung 55-inch QLED 4K smart TV.", "short_desc": "Samsung QLED TV", "unit": "pcs"},
    {"name": "LG OLED TV", "brand": "LG", "long_desc": "LG 65-inch OLED 4K smart TV with HDR.", "short_desc": "LG OLED TV", "unit": "pcs"},
]


# Generate 100 unique entries by combining base products + variations
NUM_PRODUCTS = 100
COUNTRY_ID = 1

import re

def make_slug(text):
    # lowercase, replace spaces with hyphens, remove invalid chars
    text = text.lower()
    text = re.sub(r'\s+', '-', text)         # spaces → hyphens
    text = re.sub(r'[^a-z0-9_-]', '', text) # remove invalid chars
    return text


class Command(BaseCommand):
    help = 'Insert 100 realistic products with all fields filled'

    def handle(self, *args, **kwargs):
        for i in range(1, NUM_PRODUCTS+1):
            base = random.choice(PRODUCTS)
            name = f"{base['name']} {i}"  # ensure uniqueness
            brand = base['brand']
            code = f"{name[:3].upper()}{i:03d}"
            slug = make_slug(name)
            brand_id = random.randint(1, 25)
            product_group_id = random.randint(1, 15)
            language_id = random.randint(1, 5)
            manufacturer_id = random.randint(1, 25)
            category_id = random.randint(1, 15)
            product_type_id = random.randint(1, 40)

            # Realistic numeric fields
            mpin = str(random.randint(1000, 9999))
            upc = str(random.randint(1000, 9999))
            isbn = str(random.randint(1000000000000, 9999999999999))
            ean = str(random.randint(1000000000000, 9999999999999))
            notes = f"Notes for {name}"

            # Use base descriptions
            long_description = base['long_desc']
            short_description = base['short_desc']
            unit_of_measure = base['unit']

            # search_keywords: combine all text fields
            search_keywords = ", ".join([
                name, brand, code, slug, long_description, short_description, unit_of_measure, mpin, upc, isbn, ean, notes
            ]).lower()

            Product.objects.update_or_create(
                id=i,
                defaults={
                    "name": name,
                    "code": code,
                    "status": 1,
                    "search_keywords": search_keywords,
                    "slug": slug,
                    "brand_id": brand_id,
                    "product_group_id": product_group_id,
                    "language_id": language_id,
                    "manufacturer_id": manufacturer_id,
                    "category_id": category_id,
                    "country_id": COUNTRY_ID,
                    "product_type_id": product_type_id,
                    "long_description": long_description,
                    "short_description": short_description,
                    "unit_of_measure": unit_of_measure,
                    "mpin": mpin,
                    "upc": upc,
                    "isbn": isbn,
                    "ean": ean,
                    "notes": notes,
                    "image": None,
                }
            )

        self.stdout.write(self.style.SUCCESS('Successfully inserted 100 realistic products'))
