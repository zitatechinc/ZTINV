import random
from django.core.management.base import BaseCommand
from vendor.models import Vendor, VendorBank, VendorTax
from location.models import Country
from django.db import IntegrityError

class Command(BaseCommand):
    help = 'Generate India-specific VendorBank and VendorTax data'

    def handle(self, *args, **kwargs):
        # India-specific data
        bank_names = [
            'State Bank of India', 'HDFC Bank', 'ICICI Bank', 'Axis Bank', 
            'Punjab National Bank', 'Bank of Baroda', 'Kotak Mahindra Bank', 
            'IDFC Bank', 'Yes Bank', 'Canara Bank', 'IndusInd Bank', 'RBL Bank'
        ]
        # Tax categories commonly used in India
        tax_categories = [
            'GST', 'Income Tax', 'TDS', 'Service Tax', 'Custom Duty', 'Excise Duty', 
            'Professional Tax', 'VAT', 'Luxury Tax', 'Stamp Duty', 'Securities Transaction Tax',
            'Property Tax', 'Entry Tax', 'Dividend Distribution Tax', 'Central Sales Tax',
            'State Sales Tax', 'Cess', 'Swachh Bharat Cess', 'Krishi Kalyan Cess', 'Octroi',
            'Entertainment Tax', 'Capital Gains Tax', 'Wealth Tax', 'Gift Tax', 'Fringe Benefit Tax',
            'Education Cess', 'Higher Education Cess', 'Road Tax', 'Motor Vehicle Tax', 'Luxury Car Tax',
            'Oil Cess', 'Coal Cess', 'Customs Duty', 'Import Duty', 'Export Duty',
            'Surcharge', 'Toll Tax', 'Environment Tax', 'Carbon Tax', 'Water Tax',
            'Electricity Duty', 'Professional Tax', 'Service Charge', 'Dividend Tax', 'Insurance Tax',
            'Banking Cash Transaction Tax', 'Airport Tax', 'Railway Tax', 'Telecom Tax', 'Television Tax'
        ]

        # Cities in India
        cities = [
            "Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Pune", "Ahmedabad",
            "Jaipur", "Lucknow", "Kanpur", "Nagpur", "Indore", "Thane", "Bhopal", "Visakhapatnam",
            "Vadodara", "Coimbatore", "Patna", "Ludhiana", "Agra", "Nashik", "Faridabad", "Meerut",
            "Rajkot", "Kalyan", "Vasai", "Varanasi", "Srinagar", "Aurangabad", "Dhanbad", "Amritsar",
            "Navi Mumbai", "Allahabad", "Ranchi", "Howrah", "Jabalpur", "Gwalior", "Vijayawada",
            "Jodhpur", "Madurai", "Raipur", "Kota", "Guwahati", "Chandigarh", "Solapur", "Hubli",
            "Tiruchirappalli", "Bareilly", "Mysore", "Tiruppur"
        ]

        # Streets commonly used in India
        streets = [
            "MG Road", "Park Street", "Brigade Road", "Station Road", "Ring Road", "Church Street",
            "Main Street", "Ashok Road", "Rajiv Gandhi Marg", "Connaught Place", "Jawaharlal Nehru Road",
            "Anna Salai", "MG Marg", "Kasturba Road", "Swami Vivekananda Road", "Park Avenue",
            "Marine Drive", "Netaji Subhash Road", "Gandhi Road", "Chowringhee Road", "Link Road",
            "Palace Road", "Vidhana Soudha Road", "MG Layout", "King's Road", "Queen's Road",
            "Victoria Road", "Lakshmi Road", "Station Road", "Airport Road", "Ring Road East",
            "Ring Road West", "Industrial Area Road", "Sector Road", "Market Street", "Hill Road",
            "College Road", "Flower Street", "Bazaar Street", "Temple Road", "Silk Board Road",
            "Bridge Road", "Civic Centre Road", "VIP Road", "Old Airport Road", "Kemp Fort Road",
            "Freedom Road", "Victory Road", "Garden Road"
        ]

        # Landmarks commonly used in India
        landmarks = [
            "Near Bus Stop", "Opposite Mall", "Next to Temple", "Near Metro Station", "Opposite School",
            "Next to Park", "Near Railway Station", "Opposite Hospital", "Next to Police Station",
            "Near Shopping Center", "Opposite Post Office", "Next to Bank", "Near Airport", 
            "Opposite Stadium", "Next to College", "Near Market", "Opposite Factory", "Next to Hotel",
            "Near River", "Opposite Temple", "Next to Playground", "Near Bus Stand", "Opposite Cinema",
            "Next to Petrol Pump", "Near Library", "Opposite Mall Entrance", "Next to Stadium Gate",
            "Near Toll Plaza", "Opposite Government Office", "Next to Shopping Complex", "Near Main Road",
            "Opposite Train Station", "Next to IT Park", "Near Residential Colony", "Opposite Petrol Station",
            "Next to Temple Gate", "Near Water Tank", "Opposite Bus Terminal", "Next to Community Hall",
            "Near Flyover", "Opposite Post Box", "Next to Sports Complex", "Near Metro Entrance",
            "Opposite School Gate", "Next to Public Garden", "Near Police Chowki", "Opposite Hotel Lobby",
            "Next to Hospital Entrance", "Near Shopping Arcade", "Opposite Temple Courtyard", "Next to Bus Depot"
        ]

        account_types = ['Savings', 'Current']

        india = Country.objects.filter(name='India').first()
        if not india:
            print("India not found in Country table. Please add India.")
            return

        for i in range(1, 101):  # Generate 100 records
            try:
                # Select a random vendor from DB
                vendor = Vendor.objects.order_by('?').first()
                if not vendor:
                    print("No vendors found in database.")
                    break

                # Generate VendorBank data
                bank_name = random.choice(bank_names)
                account_holder_name = f"{vendor.company_name1} A/C Holder"
                account_number = "".join([str(random.randint(0, 9)) for _ in range(10)])
                routing_number = str(random.randint(100000, 999999))
                account_type = random.choice(account_types)
                branch_name = f"{bank_name} Branch {random.randint(1, 50)}"
                ifsc_code = bank_name[:4].upper() + "0" + str(random.randint(100000, 999999))
                micr_code = "MICR" + str(random.randint(100000, 999999))
                primary = random.choice([True, False])
                swift_code = "SWIFT" + str(random.randint(100000, 999999))
                phone_number = "+91" + "".join([str(random.randint(0, 9)) for _ in range(10)])
                address = f"{random.randint(1, 999)}, {random.choice(streets)}, {random.choice(cities)}, {random.choice(landmarks)}"

                VendorBank.objects.create(
                    vendor=vendor,
                    account_holder_name=account_holder_name,
                    account_number=account_number,
                    routing_number=routing_number,
                    account_type=account_type,
                    bank_name=bank_name,
                    branch_name=branch_name,
                    ifsc_code=ifsc_code,
                    micr_code=micr_code,
                    primary=primary,
                    swift_code=swift_code,
                    phone_number=phone_number,
                    address=address
                )
                print(f"VendorBank created for {vendor.company_name1} ({account_number})")

                # Generate VendorTax data
                tax_name = random.choice(tax_categories)
                tax_number = tax_name[:2].upper() + str(random.randint(100000, 999999))
                tax_rate = round(random.uniform(0, 28), 2)  # Tax rate 0% - 28%
                other_tax_details = f"{tax_name} details for {vendor.company_name1}"

                VendorTax.objects.create(
                    vendor=vendor,
                    name=tax_name,
                    country=india,
                    category=tax_name,
                    tax_number=tax_number,
                    tax_rate=tax_rate,
                    other_tax_details=other_tax_details
                )
                print(f"VendorTax created for {vendor.company_name1} ({tax_number})")

            except IntegrityError as e:
                print(f"Error creating records for vendor {vendor.company_name1}: {e}")

        self.stdout.write(self.style.SUCCESS('Successfully generated 100 India-specific VendorBank and VendorTax records.'))
