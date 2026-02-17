import random
from django.core.management.base import BaseCommand
from catalog.models import Attribute, Category, ProductType, ProductGroup
from django.utils.text import slugify
import random
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
                          {"name": "color", "description": "Product color"},
                          {"name": "launch year", "description": "Year when the product was launched"},
                          {"name": "Model Number", "description": "Manufacturer's model number"},
                          {"name": "Series / Generation", "description": "Series or generation of the model"},
                          {"name": "Processor", "description": "CPU type and speed"},
                          {"name": "RAM", "description": "Memory capacity"},
                          {"name": "Storage", "description": "Internal storage capacity"},
                          {"name": "Screen Type / Display Type", "description": "Type of display panel"},
                          {"name": "Screen Size / Display size", "description": "Diagonal screen size in inches"},
                          {"name": "Display Resolution", "description": "Screen resolution (e.g., 4K, Full HD)"},
                          {"name": "Refresh Rate", "description": "Screen refresh rate in Hz"},
                          {"name": "Battery Capacity", "description": "Battery capacity if applicable (mAh)"},
                          {"name": "Power Consumption", "description": "Energy consumption in Watts"},
                          {"name": "Voltage / Frequency Range", "description": "Operating voltage and frequency"},
                          {"name": "Connectivity ports", "description": "Available ports (HDMI, USB, etc.)"},
                          {"name": "Operating System", "description": "OS installed on the device"},
                          {"name": "Weight With Stand", "description": "Weight including stand"},
                          {"name": "Weight Without Stand", "description": "Weight without stand"},
                          {"name": "Barcode / GTIN / UPC", "description": "Unique product identifier"},
                          {"name": "Pre installed apps", "description": "Apps preloaded on the device"},
                          {"name": "Display Technology", "description": "LCD, LED, OLED, etc."},
                          {"name": "Warranty", "description": "Warranty period"},
                          {"name": "Sensors", "description": "Built-in sensors (e.g., motion, light)"}
                        ]
                      },
                      "Refrigerator": {
                        "Category Specific": [
                          {"name": "Color", "description": "Exterior color"},
                          {"name": "Launch Year", "description": "Year when the product was launched"},
                          {"name": "Model Number", "description": "Manufacturer's model number"},
                          {"name": "Series / Generation", "description": "Series or generation of the model"},
                          {"name": "Capacity / Storage", "description": "Refrigerator storage capacity"},
                          {"name": "Compressor Type", "description": "Type of compressor used"},
                          {"name": "Shelf Type / Construction", "description": "Material and construction of shelves"},
                          {"name": "Price", "description": "Retail price"},
                          {"name": "Cooling Type", "description": "Type of cooling technology"},
                          {"name": "Refrigerant", "description": "Refrigerant gas used"},
                          {"name": "voltage", "description": "Operating voltage"},
                          {"name": "Freezer Capacity", "description": "Capacity of freezer section"},
                          {"name": "Refrigerator Capacity", "description": "Capacity of refrigerator section"},
                          {"name": "Type", "description": "Type of refrigerator (single door, double door, etc.)"},
                          {"name": "Star Rating (Energy Efficiency) / Rating", "description": "Energy efficiency rating"},
                          {"name": "Defrost Type", "description": "Manual or automatic defrost"},
                          {"name": "Smart features", "description": "IoT or smart functionalities"},
                          {"name": "Build Material", "description": "Material used for body"},
                          {"name": "Cooling Technology", "description": "Type of cooling technology"},
                          {"name": "Annual Power Consumption (kWh/year)", "description": "Energy usage per year"},
                          {"name": "Freezer Capacity (Litres)", "description": "Freezer volume in litres"},
                          {"name": "Warranty", "description": "Warranty period"}
                        ]
                      },
                      "Oven": {
                        "Category Specific": [
                          {"name": "Color", "description": "Exterior color"},
                          {"name": "launch year", "description": "Year when the product was launched"},
                          {"name": "Installation type", "description": "Built-in or freestanding"},
                          {"name": "Power Consumption", "description": "Energy consumption in Watts"},
                          {"name": "Capacity", "description": "Oven internal capacity"},
                          {"name": "Features", "description": "Special features (convection, grill, etc.)"},
                          {"name": "Voltage", "description": "Operating voltage"},
                          {"name": "Cavity", "description": "Number of cavities"},
                          {"name": "Control type", "description": "Manual or digital controls"},
                          {"name": "Turntable", "description": "Presence of rotating tray"},
                          {"name": "Child lock", "description": "Child safety feature"},
                          {"name": "Series / Generation", "description": "Series or generation of the model"},
                          {"name": "Warranty", "description": "Warranty period"}
                        ]
                      },
                      "Laptop": {
                        "Category Specific": [
                          {"name": "color", "description": "Product color"},
                          {"name": "launch year", "description": "Year when the product was launched"},
                          {"name": "Model Number", "description": "Manufacturer's model number"},
                          {"name": "Series / Generation", "description": "Series or generation of the model"},
                          {"name": "Processor", "description": "CPU type and speed"},
                          {"name": "RAM", "description": "Memory capacity"},
                          {"name": "Storage", "description": "Internal storage capacity"},
                          {"name": "Screen Size / Display Type", "description": "Diagonal screen size and display type"},
                          {"name": "Resolution", "description": "Screen resolution"},
                          {"name": "Refresh Rate", "description": "Screen refresh rate in Hz"},
                          {"name": "Battery Capacity", "description": "Battery capacity in mAh or Wh"},
                          {"name": "Power Consumption", "description": "Energy usage in Watts"},
                          {"name": "Voltage / Frequency Range", "description": "Operating voltage and frequency"},
                          {"name": "Connectivity", "description": "Available ports and wireless connectivity"},
                          {"name": "Operating System", "description": "Preinstalled OS"},
                          {"name": "Warranty", "description": "Warranty period"},
                          {"name": "Sensors", "description": "Built-in sensors"}
                        ]
                      },
                      "Dishwasher": {
                        "Category Specific": [
                          {"name": "Color", "description": "Exterior color"},
                          {"name": "Launch Year", "description": "Year when the product was launched"},
                          {"name": "Model Number", "description": "Manufacturer's model number"},
                          {"name": "Install type", "description": "Built-in or freestanding"},
                          {"name": "Washing type", "description": "Washing technology used"},
                          {"name": "Performance", "description": "Performance rating or efficiency"},
                          {"name": "Noise Level", "description": "Operating noise in dB"},
                          {"name": "Control type", "description": "Manual or digital controls"},
                          {"name": "Capacity", "description": "Number of place settings"},
                          {"name": "Water Consumption per Cycle", "description": "Water used per washing cycle"},
                          {"name": "Power Consumption", "description": "Energy used per cycle"},
                          {"name": "Drain pump", "description": "Type of drain pump"},
                          {"name": "Operating System", "description": "OS if smart dishwasher"}
                        ]
                      },
                      "Mobile": {
                        "Category Specific": [
                          {"name": "Model Number", "description": "Manufacturer's model number"},
                          {"name": "launch year", "description": "Year when the product was launched"},
                          {"name": "color", "description": "Phone color"},
                          {"name": "Processor", "description": "CPU type and speed"},
                          {"name": "RAM", "description": "Memory capacity"},
                          {"name": "Storage", "description": "Internal storage capacity"},
                          {"name": "Screen Size", "description": "Diagonal screen size"},
                          {"name": "Display Type", "description": "Type of display panel"},
                          {"name": "Camera", "description": "Rear and front camera specs"},
                          {"name": "Battery Capacity", "description": "Battery size in mAh"},
                          {"name": "Sensors", "description": "Built-in sensors"},
                          {"name": "Connectivity Features", "description": "Wireless and wired connectivity"},
                          {"name": "Refresh rate", "description": "Screen refresh rate in Hz"},
                          {"name": "Operating System", "description": "Preinstalled OS"},
                          {"name": "Resolution", "description": "Display resolution"},
                          {"name": "ze", "description": "Screen aspect ratio or feature code"},
                          {"name": "Warranty", "description": "Warranty period"},
                          {"name": "IP rating", "description": "Ingress Protection rating"}
                        ]
                      }
                    }
                  },
                  "HAWA(Trading Goods)": {
                    "Electronics": {
                      "Washing Machine": {
                        "Category Specific": [
                          {"name": "color", "description": "Product color"},
                          {"name": "launch year", "description": "Year when the product was launched"},
                          {"name": "Model Number", "description": "Manufacturer's model number"},
                          {"name": "Series / Generation", "description": "Series or generation of the model"},
                          {"name": "Capacity", "description": "Washing capacity in kg"},
                          {"name": "Loading Type", "description": "Front or top load"},
                          {"name": "Max RPM", "description": "Maximum spin speed"},
                          {"name": "Num of Cycles / Programs", "description": "Number of wash programs"},
                          {"name": "Num of Wash / Rinse Temps", "description": "Temperature options for wash/rinse"},
                          {"name": "Smart Features", "description": "IoT or app-based control"},
                          {"name": "Wash Technology", "description": "Type of washing technology"},
                          {"name": "Digital Display / Touch Panel", "description": "Type of control panel"},
                          {"name": "Motor Type", "description": "Type of motor used"},
                          {"name": "Warranty", "description": "Warranty period"},
                          {"name": "Star Rating (Energy Efficiency)", "description": "Energy efficiency rating"},
                          {"name": "Water Consumption (Litres per cycle)", "description": "Water used per wash cycle"}
                        ]
                      }
                    }
                  },
                    "ROH (Raw Material)": {
                    "Chemicals": {}
                    },
                    "HALB (Semi-finished)": {
                    "Fabric Rolls": {}
                    },
                    "DIEN (Services)": {
                    "office services": {}
                    }
                 
                }


        """
        Recursive function to iterate JSON and insert attributes into the DB.
        """
        Attribute.objects.all().delete()

        for product_type, groups in ATTRIBUTE_JSON.items():
            if product_type == "ALL":
                pt_obj = None
            else:
                pt_obj = ProductType.objects.filter(name=product_type).first()
            
            for product_group, categories in groups.items():
                if product_group == "ALL":
                    pg_obj = None
                else:
                    pg_obj = ProductGroup.objects.filter(name=product_group).first()
                
                for category, attr_types in categories.items():
                    if category == "ALL":
                        cat_obj = None
                    else:
                        cat_obj = Category.objects.filter(name=category).first()
                    
                    for attribute_type, attributes in attr_types.items():
                        for attr in attributes:
                            name = attr['name']
                            description = attr.get('description', '')
                            code = generate_unique_code(name, cat_obj.name if cat_obj else 'PC', pg_obj.name if pg_obj else 'PG', pt_obj.name if pt_obj else 'PT')
                            
                            Attribute.objects.update_or_create(
                                name=name,
                                defaults={
                                    "code": code,
                                    "description": description,
                                    "category": cat_obj,
                                    "product_type": pt_obj,
                                    "product_group": pg_obj,
                                    "attribute_type": attribute_type,
                                    "status" : 1
                                }
                            )

    # # Run the insertion


    #     self.stdout.write(self.style.SUCCESS(f"✅ Successfully created {len(attributes)} Attributes"))
