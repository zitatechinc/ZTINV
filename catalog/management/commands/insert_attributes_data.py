import random
from django.core.management.base import BaseCommand
from catalog.models import Attribute, Category, ProductType, ProductGroup
from django.utils.text import slugify
from django.core.exceptions import ValidationError

def generate_unique_code(name, category_name, group_name, product_type_name):
    """
    Generates a unique code based on attribute name, category, group, and type.
    Uses slugify and adds a hash suffix if needed.
    """
    base_code = f"{slugify(name)[:3]}-{slugify(category_name)[:5]}-{slugify(group_name)[:3]}-{slugify(product_type_name)[:3]}-{random.randint(1,5)}{random.randint(1,5)}".upper()
    code = base_code
    counter = 1

    # Check if code already exists
    while Attribute.objects.filter(code=code).exists():
        code = f"{base_code}_{counter}"
        counter += 1
    
    return code

class Command(BaseCommand):
    help = "Seed database with 100+ Attributes based on both Category and Product Type"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("🚀 Creating attributes by Category + Product Type..."))
        
        ATTRIBUTE_JSON = {
             "ALL": {
                    "ALL": {
                      "ALL": {
                        "Common": [
                          {"name": "Short Description", "description": "Brief summary of the product"},
                          {"name": "Long Description", "description": "Detailed description of the product"},
                          {"name": "Brand / Manufacturer Name", "description": "Brand or manufacturer of the product"},
                          {"name": "Base unit of measure", "description": "Unit used to measure product quantity"},
                          {"name": "Dimensions (Length, Width, Height)", "description": "Physical dimensions of the product"},
                          {"name": "Dimensions unit", "description": "Unit for dimensions (cm, inch, etc.)"},
                          {"name": "MPN", "description": "Manufacturer Part Number"},
                          {"name": "UPC", "description": "Universal Product Code"},
                          {"name": "EAN", "description": "European Article Number"},
                          {"name": "Gross Weight", "description": "Weight including packaging"},
                          {"name": "Net Weight", "description": "Weight without packaging"},
                          {"name": "Unit of Weight", "description": "Unit for weight measurement (kg, g, etc.)"},
                          {"name": "Currency", "description": "Currency used for pricing"},
                          {"name": "Price", "description": "Retail price of the product"},
                          {"name": "Country of Origin", "description": "Country where the product was manufactured"},
                          {"name": "Created Date", "description": "Date the product record was created"},
                          {"name": "Last Updated Date", "description": "Date the product record was last updated"},
                          {"name": "Source (PDF/URL)", "description": "Reference source for product data"}
                        ]
                      }
                    }
                  },
            "FERT(Finished Goods)": {
                "Electronics": {
                    "TV": {
                        "Category Specific": [
                            {"name": "color", "description": "Product color", "search_keywords": "color, product, TV color"},
                            {"name": "launch year", "description": "Year launched", "search_keywords": "launch year, TV, model year"},
                            {"name": "Model Number", "description": "Manufacturer's model number", "search_keywords": "model number, TV model"},
                            {"name": "Processor", "description": "CPU type and speed", "search_keywords": "processor, CPU, speed"},
                            {"name": "RAM", "description": "Memory capacity", "search_keywords": "RAM, memory, TV specs"},
                            {"name": "Storage", "description": "Internal storage capacity", "search_keywords": "storage, TV storage"},
                            {"name": "Screen Size", "description": "Diagonal screen size", "search_keywords": "screen size, TV size, display size"},
                            {"name": "Display Resolution", "description": "Screen resolution (e.g., 4K, Full HD)", "search_keywords": "resolution, screen resolution, TV resolution"},
                            {"name": "Battery Capacity", "description": "Battery capacity if applicable", "search_keywords": "battery, capacity, battery size"},
                            {"name": "Warranty", "description": "Warranty period", "search_keywords": "warranty, TV warranty"},
                            # NEW attributes
                            {"name": "Refresh Rate", "description": "Screen refresh rate in Hz", "search_keywords": "refresh rate, TV refresh rate, screen refresh"},
                            {"name": "HDR Support", "description": "High Dynamic Range support", "search_keywords": "HDR, high dynamic range, TV HDR"},
                            {"name": "Smart TV Features", "description": "Smart TV functionalities", "search_keywords": "smart TV, TV features, smart features"},
                            {"name": "Connectivity Ports", "description": "HDMI, USB, Ethernet ports", "search_keywords": "ports, HDMI, USB, Ethernet"}
                        ]
                    },
                    "Refrigerator": {
                        "Category Specific": [
                            {"name": "Color", "description": "Exterior color", "search_keywords": "color, refrigerator color, exterior color"},
                            {"name": "Capacity", "description": "Refrigerator storage capacity", "search_keywords": "capacity, storage, refrigerator capacity"},
                            {"name": "Compressor Type", "description": "Type of compressor used", "search_keywords": "compressor, refrigerator compressor"},
                            {"name": "Cooling Type", "description": "Type of cooling technology", "search_keywords": "cooling, refrigerator cooling, cooling technology"},
                            {"name": "Warranty", "description": "Warranty period", "search_keywords": "warranty, refrigerator warranty"},
                            # NEW attributes
                            {"name": "Number of Doors", "description": "Single, double, or multi-door refrigerator", "search_keywords": "number of doors, refrigerator doors"},
                            {"name": "Energy Rating", "description": "Star rating for energy efficiency", "search_keywords": "energy rating, refrigerator energy, star rating"},
                            {"name": "Defrost Type", "description": "Manual or automatic defrost", "search_keywords": "defrost, automatic defrost, manual defrost"},
                            {"name": "Smart Features", "description": "IoT or app-based features", "search_keywords": "smart features, IoT, refrigerator smart features"}
                        ]
                    },
                    "Laptop": {
                        "Category Specific": [
                            {"name": "color", "description": "Laptop color", "search_keywords": "color, laptop color"},
                            {"name": "launch year", "description": "Year launched", "search_keywords": "launch year, laptop launch"},
                            {"name": "Model Number", "description": "Manufacturer's model number", "search_keywords": "model number, laptop model"},
                            {"name": "Processor", "description": "CPU type and speed", "search_keywords": "processor, CPU, laptop processor"},
                            {"name": "RAM", "description": "Memory capacity", "search_keywords": "RAM, memory, laptop RAM"},
                            {"name": "Storage", "description": "Internal storage capacity", "search_keywords": "storage, laptop storage"},
                            {"name": "Screen Size / Display Type", "description": "Diagonal screen size and display type", "search_keywords": "screen size, display type, laptop screen"},
                            {"name": "Resolution", "description": "Screen resolution", "search_keywords": "resolution, laptop resolution"},
                            {"name": "Battery Capacity", "description": "Battery capacity in mAh or Wh", "search_keywords": "battery, laptop battery"},
                            {"name": "Warranty", "description": "Warranty period", "search_keywords": "warranty, laptop warranty"},
                            # NEW attributes
                            {"name": "Graphics Card", "description": "Dedicated or integrated GPU", "search_keywords": "graphics card, laptop GPU"},
                            {"name": "Operating System", "description": "Pre-installed OS", "search_keywords": "operating system, laptop OS"},
                            {"name": "Keyboard Type", "description": "Backlit, mechanical, etc.", "search_keywords": "keyboard, backlit keyboard, mechanical keyboard"},
                            {"name": "Weight", "description": "Laptop weight in kg", "search_keywords": "weight, laptop weight"}
                        ]
                    }
                }
            },
            "HAWA(Trading Goods)": {
                "Electronics": {
                    "Washing Machine": {
                        "Category Specific": [
                            {"name": "color", "description": "Product color", "search_keywords": "color, washing machine color"},
                            {"name": "launch year", "description": "Year launched", "search_keywords": "launch year, washing machine launch"},
                            {"name": "Model Number", "description": "Manufacturer's model number", "search_keywords": "model number, washing machine model"},
                            {"name": "Capacity", "description": "Washing capacity in kg", "search_keywords": "capacity, washing machine capacity"},
                            {"name": "Loading Type", "description": "Front or top load", "search_keywords": "loading type, washing machine load type"},
                            {"name": "Max RPM", "description": "Maximum spin speed", "search_keywords": "spin speed, washing machine speed"},
                            {"name": "Warranty", "description": "Warranty period", "search_keywords": "warranty, washing machine warranty"},
                            # NEW attributes
                            {"name": "Number of Programs", "description": "Number of washing programs", "search_keywords": "programs, washing programs"},
                            {"name": "Energy Rating", "description": "Star rating for energy efficiency", "search_keywords": "energy rating, washing machine energy"},
                            {"name": "Water Consumption", "description": "Litres per cycle", "search_keywords": "water consumption, washing machine water"},
                            {"name": "Noise Level", "description": "Operating noise in dB", "search_keywords": "noise level, washing machine noise"}
                        ]
                    }
                }
            }
        }

        # Iterate over the attribute data and insert/update
        for product_type, groups in ATTRIBUTE_JSON.items():
            pt_obj = ProductType.objects.filter(name=product_type).first()

            for product_group, categories in groups.items():
                pg_obj = ProductGroup.objects.filter(name=product_group).first()

                for category, attr_types in categories.items():
                    cat_obj = Category.objects.filter(name=category).first()

                    for attribute_type, attributes in attr_types.items():
                        for attr in attributes:
                            name = attr['name']
                            description = attr.get('description', '')
                            search_keywords = attr.get('search_keywords', '')
                            code = generate_unique_code(name, cat_obj.name if cat_obj else 'PC', pg_obj.name if pg_obj else 'PG', pt_obj.name if pt_obj else 'PT')

                            try:
                                # Check if attribute exists by name and the combination of category, product_type, and product_group
                                existing_attribute = Attribute.objects.filter(
                                    name=name,
                                    category=cat_obj,
                                    product_type=pt_obj,
                                    product_group=pg_obj
                                ).first()

                                if existing_attribute:
                                    # Update the existing attribute
                                    existing_attribute.code = code
                                    existing_attribute.description = description
                                    existing_attribute.search_keywords = search_keywords
                                    existing_attribute.slug = slugify(name)
                                    existing_attribute.save()
                                    self.stdout.write(f"Updated Attribute: {existing_attribute.name} | Code: {existing_attribute.code}")
                                else:
                                    # If it doesn't exist, create a new one
                                    new_attribute = Attribute.objects.create(
                                        name=name,
                                        code=code,
                                        description=description,
                                        search_keywords=search_keywords,
                                        category=cat_obj,
                                        product_type=pt_obj,
                                        product_group=pg_obj,
                                        attribute_type=attribute_type,
                                        status=1,
                                        slug=slugify(name)
                                    )
                                    self.stdout.write(f"Created Attribute: {new_attribute.name} | Code: {new_attribute.code}")
                            
                            except ValidationError as e:
                                # Log the error if validation fails
                                self.stdout.write(self.style.ERROR(f"Error creating attribute: {name} - {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f"✅ Successfully created/updated attributes"))
