from django.core.management.base import BaseCommand
from vendor.models import VendorType  # Assuming your VendorType model is defined in the catalog app
from django.db import IntegrityError
import random

class Command(BaseCommand):
    help = 'Generate 100 real-time VendorType data with name, code, status, and description'

    def handle(self, *args, **kwargs):
        # Real-world vendor types with descriptions (100 different types)
        vendor_types = [
            ("Manufacturer", "A company that manufactures goods from raw materials."),
            ("Distributor", "A business that buys products from manufacturers and sells them to retailers."),
            ("Retailer", "A business that sells goods directly to consumers."),
            ("Wholesaler", "A business that sells products in bulk to retailers."),
            ("Service Vendor", "A company providing specialized services to other businesses."),
            ("Logistics Provider", "A company handling the transportation and storage of goods."),
            ("Technology Provider", "A company that sells technology-related products or services."),
            ("Consultancy", "A company offering expert advice in a particular field."),
            ("Healthcare Supplier", "A business that provides medical supplies and equipment."),
            ("Food Supplier", "A company that supplies raw and processed food products."),
            ("Energy Supplier", "A company providing energy like electricity, gas, or renewable energy."),
            ("Telecommunications", "A company providing phone and internet services."),
            ("Finance Vendor", "A company offering financial products or services to businesses."),
            ("Legal Services", "A firm that provides legal services to individuals or organizations."),
            ("Insurance Provider", "A company providing various types of insurance products."),
            ("Construction Vendor", "A company supplying construction materials and services."),
            ("Automotive Supplier", "A company that provides parts and accessories for the automotive industry."),
            ("Textile Supplier", "A company that supplies fabrics and textile products."),
            ("Packaging Vendor", "A business that provides packaging solutions for products."),
            ("Raw Materials Supplier", "A vendor supplying raw materials for manufacturing."),
            ("Import/Export Vendor", "A business specializing in the import and export of goods."),
            ("Temporary Vendor", "A vendor contracted for a short-term or project-specific task."),
            ("Internal Vendor", "A company that provides services or goods internally within the same organization."),
            ("Environmental Services", "A company offering solutions related to waste management, recycling, and environmental sustainability."),
            ("Security Services", "A business offering physical and cybersecurity services."),
            ("Cleaning Services", "A company providing commercial and residential cleaning services."),
            ("Printing Vendor", "A company that offers printing services for businesses or consumers."),
            ("Transportation", "A business providing transportation services like freight and passenger transport."),
            ("Real Estate Services", "A vendor offering services related to the sale, purchase, and management of real estate."),
            ("IT Support Vendor", "A company that provides IT services, such as software support, hardware maintenance, etc."),
            ("Advertising Agency", "A firm that provides advertising and marketing services to businesses."),
            ("Publishing Vendor", "A company that publishes books, newspapers, magazines, and other media."),
            ("Agricultural Supplier", "A business that provides agricultural products, tools, and services."),
            ("Wholesale Distributor", "A vendor that distributes goods in large quantities to businesses."),
            ("Medical Equipment Supplier", "A business supplying medical devices and instruments."),
            ("Hospitality Services", "A company offering services like hotel accommodations, food services, etc."),
            ("Event Management", "A company specializing in organizing and managing events."),
            ("Software Vendor", "A company that provides software solutions, including SaaS and enterprise software."),
            ("Hardware Supplier", "A company that provides hardware products like computers, machines, etc."),
            ("Retail Management Systems", "A company offering software and systems for managing retail operations."),
            ("Laboratory Equipment Supplier", "A company providing scientific and laboratory equipment."),
            ("Packaging Material Supplier", "A company providing packaging materials like boxes, wraps, and containers."),
            ("Furniture Supplier", "A company supplying office and home furniture."),
            ("Cleaning Equipment Supplier", "A business that provides industrial-grade cleaning equipment."),
            ("Security Equipment Supplier", "A company providing security systems like cameras, alarms, etc."),
            ("Waste Management", "A company providing waste disposal and recycling services."),
            ("Advertising Materials Supplier", "A company providing advertising materials such as banners, flyers, and digital ads."),
            ("Entertainment Services", "A company providing entertainment services such as music, theater, etc."),
            ("Business Consulting", "A business that provides strategic advice to other businesses."),
            ("Freight Forwarding", "A business that manages the shipment of goods for customers."),
            ("Courier Services", "A company that provides quick, reliable shipping and delivery services."),
            ("Cleaning Supplies", "A vendor that provides cleaning chemicals, tools, and supplies."),
            ("Food Packaging", "A company that specializes in packaging food products."),
            ("Security Services Vendor", "A vendor that provides physical or cyber security services."),
            ("Distribution Management", "A company providing solutions for distribution logistics and management."),
            ("R&D Vendor", "A business that provides research and development services for companies."),
            ("Professional Training Services", "A company that offers corporate or professional training programs."),
            ("Utility Supplier", "A company that provides utilities like water, gas, and electricity."),
            ("Real Estate Developer", "A business that develops residential, commercial, or industrial properties."),
            ("Chemical Supplier", "A company that supplies chemicals for industrial, agricultural, or scientific use."),
            ("Plastic Supplier", "A business that supplies plastic materials for manufacturing."),
            ("Metal Supplier", "A company providing metal products such as steel, copper, aluminum."),
            ("Luxury Goods Supplier", "A company that supplies high-end, luxury goods like watches, jewelry, etc."),
            ("Building Materials Supplier", "A vendor that supplies materials like cement, bricks, tiles."),
            ("Printing and Packaging", "A business that handles both printing and packaging of products."),
            ("Fleet Services", "A company offering fleet management services for vehicles."),
            ("Pet Supplies", "A business that supplies pet products and services."),
            ("Apparel Supplier", "A company that provides clothing and textile products."),
            ("Bulk Supplier", "A vendor that supplies products in bulk for resellers."),
            ("Tool Supplier", "A business that provides tools and machinery for various industries."),
            ("Petroleum Supplier", "A company providing oil, gas, and other petroleum products."),
            ("Heavy Equipment Supplier", "A business providing machinery and equipment for construction and mining."),
            ("Mobile Vendor", "A business providing mobile products and services."),
            ("Office Equipment Supplier", "A company supplying office furniture and equipment."),
            ("Healthcare Consultant", "A vendor providing consultancy services to healthcare providers."),
            ("B2B Software Vendor", "A company offering software solutions designed for business-to-business transactions."),
            ("Furniture Manufacturer", "A vendor involved in the production and supply of furniture."),
            ("Construction Services", "A company providing construction and engineering services."),
            ("Property Maintenance", "A business offering property maintenance services like repairs and cleaning."),
            ("Audio-Visual Supplier", "A company providing audio and visual equipment for businesses and events."),
            ("Luxury Vehicle Supplier", "A vendor providing high-end and luxury vehicles."),
            ("Chemical Distributor", "A company that distributes chemical products to industries."),
            ("Wholesale Supplier", "A business providing wholesale products to retailers and other vendors."),
            ("Green Energy Supplier", "A company that provides renewable energy solutions like solar, wind."),
            ("Data Storage Services", "A vendor offering data storage and cloud services."),
            ("Metal Fabrication", "A company specializing in the process of metalworking and fabrication."),
            ("Furniture Retailer", "A vendor that sells furniture directly to consumers."),
            ("Packaging Design", "A company offering packaging design services for products."),
            ("Industrial Equipment Supplier", "A vendor providing industrial machinery and tools."),
            ("Construction Materials", "A company supplying raw materials used in construction projects."),
            ("Warehouse Services", "A company providing warehouse management and storage solutions."),
            ("Insurance Vendor", "A company providing a variety of insurance products to individuals and businesses."),
            ("Paper Supplier", "A business supplying paper products for commercial and industrial use."),
            ("Bulk Goods Supplier", "A company that provides bulk goods like grains, chemicals, etc."),
            ("Building Maintenance", "A company that provides maintenance services for buildings and facilities."),
            ("Printing Solutions", "A company providing printing solutions for businesses."),
            ("Petroleum Supplier", "A company providing oil and gas for industrial and consumer use."),
            ("Wholesale Electronics", "A company providing electronics and gadgets at wholesale prices."),
            ("Furniture Retailer", "A business selling furniture to consumers directly."),
            ("Building Automation", "A vendor offering systems for automating building processes."),
            ("Farm Equipment Supplier", "A company providing agricultural machinery and equipment."),
            ("Travel Services", "A company providing travel-related services for businesses or individuals."),
            ("Plastic Products Supplier", "A vendor supplying plastic products for manufacturing.")
        ]

        # Generate 100 records
        for i in range(1, 101):
            # Randomly choose from the vendor types
            vendor_type_name, description = random.choice(vendor_types)
            
            # Generate the code with the prefix 'VT-' followed by a unique identifier
            code = f"VT-{vendor_type_name[:3].upper()}-{i:03d}"  # Example: VT-MAN-001, VT-DIS-002, etc.
            
            # Determine status: Randomly set Active (1) or Inactive (0)
            status = random.choice([0, 1])  # 1 for Active, 0 for Inactive
            
            # Check if VendorType with this name already exists to avoid duplicates
            if VendorType.objects.filter(name=vendor_type_name).exists():
                print(f"VendorType with name {vendor_type_name} already exists.")
                continue  # Skip creating this vendor type if it already exists

            # Create the vendor type
            try:
                VendorType.objects.create(
                    name=vendor_type_name,
                    code=code,
                    status=status,
                    description=description
                )
                print(f"VendorType '{vendor_type_name}' with code '{code}' created successfully.")
            except IntegrityError as e:
                print(f"Failed to create VendorType '{vendor_type_name}' with code '{code}' due to integrity error: {e}")

        self.stdout.write(self.style.SUCCESS('Successfully generated 100 real-time VendorType data with name, code, status, and description.'))
