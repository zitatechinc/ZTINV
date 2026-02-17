import random
import re
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from vendor.models import Vendor, VendorType  # Assuming you have a Vendor model defined
from location.models import Country, Location, SubLocation
from django.utils.text import slugify
from catalog.models import Languages

# Real-world vendor company names (examples of actual B2B suppliers/vendors)
REAL_VENDORS = [
    "Siemens", "Bosch", "GE Appliances", "Mitsubishi Electric", "Honeywell",
    "Schneider Electric", "3M", "Ford Motor Company", "Caterpillar Inc.", 
    "Emerson Electric", "United Technologies", "ABB", "BASF", "Dow Chemicals", 
    "IKEA", "Alibaba Group", "Walmart Inc.", "Amazon Supply", "Home Depot", 
    "DHL", "UPS", "FedEx", "Xerox", "Samsung Electronics", "LG Electronics", 
    "Cisco Systems", "Intel Corporation", "Hewlett-Packard", "Adobe Systems",
    "Vizio", "Sony Corporation", "Panasonic", "Philips", "Toshiba", "Sharp",
    "Rockwell Automation", "DuPont", "Lockheed Martin", "Boeing", "Northrop Grumman",
    "Raytheon Technologies", "Tyco International", "Lennox International", "Rheem Manufacturing",
    "S&P Global", "Marriott International", "Oracle", "SAP", "Dell Technologies", "Qualcomm",
    "Nokia", "Ericsson", "LG Display", "Hitachi", "NEC Corporation", "Canon Inc.",
    "Seiko", "Bridgestone", "Toyota Industries", "Honda Motors", "Fiat Chrysler",
    "PepsiCo", "Coca-Cola", "Nestle", "Unilever", "Procter & Gamble", "Johnson & Johnson",
    "Medtronic", "Siemens Healthineers", "Baxter International", "GE Healthcare",
    "ABB Robotics", "Schneider Automation", "Honeywell Process Solutions", "3M Industrial",
    "ExxonMobil", "Chevron", "Royal Dutch Shell", "BP", "TotalEnergies", "ConocoPhillips",
    "Schlumberger", "Halliburton", "Baker Hughes", "Caterpillar Machinery", "Komatsu",
    "Volvo Group", "MAN Truck & Bus", "Scania AB", "Tesla", "SpaceX", "Blue Origin",
    "Northvolt", "BYD Company", "NIO Inc.", "Xiaomi", "Huawei Technologies", "Lenovo",
    "ASUS", "Acer", "MSI", "Western Digital", "Seagate Technology", "Kingston Technology",
    "Honeywell Building Technologies", "Johnson Controls", "Siemens Building Technologies",
    "Alstom", "Bombardier", "Hitachi Rail", "CRRC Corporation", "Kone", "Otis Elevator",
    "Schindler Group", "Thyssenkrupp", "SKF Group", "Embraer", "Dassault Aviation",
    "Safran", "Rolls-Royce", "GE Aviation", "Pratt & Whitney", "MTU Aero Engines",
    "Raytheon Missiles", "Northrop Grumman Innovation", "BAE Systems", "Lockheed Martin Missiles",
    "Textron", "Honeywell Aerospace", "Rockwell Collins", "Medtronic Diabetes", "Philips Healthcare",
    "Siemens Mobility", "GE Transportation", "ABB Power", "Schneider Electric Grid", "Hitachi Energy",
    "Siemens Energy", "Schlumberger Oilfield", "Halliburton Services", "Baker Hughes Energy",
    "Cargill", "Archer Daniels Midland", "Bunge Limited", "Louis Dreyfus Company", "Olam International",
    "Wilmar International", "Dole Food Company", "Del Monte Foods", "Pepsi Lipton", "Nestle Waters",
    "Mars Inc.", "Mondelez International", "Kraft Heinz", "General Mills", "Unilever Foods",
    "L'Oréal", "Estée Lauder", "Procter & Gamble Beauty", "Reckitt Benckiser", "Colgate-Palmolive",
    "Johnson & Johnson Consumer", "Kimberly-Clark", "Henkel", "3M Consumer Products", "Sony Electronics",
    "Samsung Display", "LG Electronics Appliances", "Panasonic Industrial Solutions", "Toshiba Electronic Devices",
    "Sharp Corporation", "Canon Imaging", "Nikon", "Ricoh", "Fujifilm", "Olympus Corporation",
    "Hitachi Construction Machinery", "Komatsu Ltd.", "Volvo Construction Equipment", "Caterpillar Construction",
    "John Deere", "Kubota", "Doosan Infracore", "Terex Corporation", "Liebherr Group", "Sandvik", "Atlas Copco",
    "Honeywell Safety", "Siemens Digital Industries", "Schneider Automation", "Rockwell Automation Factory",
    "ABB Electrification", "Emerson Automation Solutions", "Mitsubishi Electric Automation", "Omron Corporation",
    "Keyence Corporation", "Fanuc", "Yaskawa Electric", "KUKA Robotics", "Denso Corporation", "Bosch Rexroth",
    "SICK AG", "Balluff", "Festo", "Pilz", "Phoenix Contact", "Weidmüller", "HARTING Technology", "Pepperl+Fuchs",
    "Beckhoff Automation", "Siemens Health", "GE Healthcare Imaging", "Philips Medical Systems", "Canon Medical",
    "Fujifilm Healthcare", "Hitachi Medical Systems", "Mindray Medical", "Medtronic", "Boston Scientific", "Abbott Labs",
    "Baxter International", "Stryker Corporation", "Zimmer Biomet", "Smith & Nephew", "Edwards Lifesciences", "Terumo",
    "Cardinal Health", "McKesson", "Henry Schein", "Owens & Minor", "Patterson Companies", "Walgreens Boots Alliance",
    "CVS Health", "Roche Diagnostics", "Siemens Diagnostics", "Beckman Coulter", "Bio-Rad Laboratories", "Thermo Fisher Scientific",
    "Agilent Technologies", "PerkinElmer", "Bruker", "GE Life Sciences", "Lonza Group", "WuXi AppTec", "Samsung Biologics",
    "Pfizer", "Moderna", "Johnson & Johnson Pharma", "Novartis", "Roche Pharma", "Sanofi", "AstraZeneca", "GSK",
    "Merck & Co.", "Bayer Pharma", "Eli Lilly", "AbbVie", "Amgen", "Biogen", "Regeneron Pharmaceuticals"
]

STATUS_CHOICES = [
    (-1, "Inactive"),
    (0, "Draft"),
    (1, "Active"),
]

import random

def generate_vendor_note():
    notes = [
        "Vendor delivered products ahead of schedule.",
        "Payment terms agreed upon: Net 30.",
        "Vendor requested updated PO for next quarter.",
        "Pending approval for bulk discount request.",
        "Vendor offered extended warranty on electronics.",
        "Shipment delayed due to customs clearance.",
        "Vendor requested feedback on recent delivery quality.",
        "Negotiated lower rates for recurring orders.",
        "Vendor updated product catalog for the new fiscal year.",
        "Received confirmation of order fulfillment.",
        "Vendor requested early payment discount.",
        "Quality check flagged minor defects in batch shipment.",
        "Vendor confirmed compliance with safety regulations.",
        "Requested vendor invoice for accounting purposes.",
        "Vendor scheduled training session for staff on product usage.",
        "Received vendor samples for evaluation.",
        "Vendor confirmed availability of high-demand items.",
        "Vendor agreed to adjust delivery schedule to match project timeline.",
        "Followed up on pending quotation for next order.",
        "Vendor requested updated company contact details.",
        "Received acknowledgment for returned shipment.",
        "Vendor suggested alternative sourcing options for critical items.",
        "Vendor requested to review contract renewal terms.",
        "Vendor reported temporary supply shortage.",
        "Confirmed vendor shipment tracking details.",
        "Vendor provided updated technical specifications.",
        "Vendor requested rescheduling of delivery due to holiday closures.",
        "Negotiated additional free units for bulk order.",
        "Vendor requested feedback on recent collaboration.",
        "Vendor updated certificates of compliance for products.",
        "Followed up on warranty claim for defective products.",
        "Vendor requested confirmation of purchase order.",
        "Received vendor's updated banking information.",
        "Vendor notified of upcoming price changes.",
        "Confirmed vendor participation in upcoming trade show.",
        "Vendor requested delivery address clarification.",
        "Vendor sent promotional material for new product launch.",
        "Followed up on late shipment from vendor.",
        "Vendor provided a replacement for damaged items.",
        "Vendor requested early release of payment to expedite delivery.",
        "Vendor updated lead time for critical components.",
        "Confirmed vendor compliance with ESG standards.",
        "Vendor requested adjustment to packaging specifications.",
        "Vendor sent updated pricing list for review.",
        "Followed up on pending order confirmation.",
        "Vendor agreed to provide training support for installation.",
        "Vendor provided shipment delay notice due to logistics issue.",
        "Confirmed vendor's capacity to handle increased order volume.",
        "Vendor requested to schedule a quarterly review meeting.",
        "Received vendor acknowledgment for received payment.",
        "Vendor requested clarification on invoice discrepancies.",
        "Vendor sent documentation for regulatory compliance.",
        "Confirmed vendor's readiness for seasonal demand spike.",
        "Vendor requested updated delivery instructions.",
        "Vendor provided guidance on product installation.",
        "Vendor suggested alternative shipping options to reduce cost.",
        "Followed up with vendor on pending certification.",
        "Vendor requested updated forecast for upcoming orders.",
        "Vendor provided status update on backordered items.",
        "Vendor notified of pending contract renewal.",
        "Vendor requested confirmation on product specification changes.",
        "Vendor agreed to provide promotional discounts for large orders.",
        "Vendor reported improvements in production lead time.",
        "Vendor requested inspection of returned defective goods.",
        "Confirmed vendor readiness for urgent order fulfillment.",
        "Vendor requested signing of updated NDA agreement.",
        "Vendor sent test samples for evaluation of new product.",
        "Vendor requested invoice correction due to pricing update.",
        "Vendor confirmed availability of new SKUs.",
        "Vendor notified of upcoming delivery window changes.",
        "Vendor requested confirmation of PO amendments.",
        "Followed up on vendor's support for installation issues.",
        "Vendor suggested alternative suppliers for out-of-stock items.",
        "Vendor requested meeting to discuss strategic partnership.",
        "Vendor provided documentation for product traceability.",
        "Vendor requested extension on delivery deadline.",
        "Confirmed vendor agreement to service level terms.",
        "Vendor sent updated shipping schedule for upcoming quarter.",
        "Vendor requested feedback on recent payment process.",
        "Vendor reported temporary production halt due to maintenance.",
        "Vendor requested clarification on contract scope.",
        "Vendor provided replacement parts for defective shipment.",
        "Vendor confirmed updated lead times for critical orders.",
        "Vendor requested advance notice for peak season demand.",
        "Vendor sent updated contact list for logistics coordination.",
        "Vendor requested confirmation of new product launch timeline.",
        "Vendor notified of quality compliance inspection date.",
        "Vendor requested assistance with customs documentation.",
        "Vendor sent updated delivery receipt for verification.",
        "Vendor requested invoice approval to proceed with production.",
        "Vendor confirmed readiness for emergency order dispatch.",
        "Vendor requested clarification on packaging labeling requirements.",
        "Vendor notified of pending performance review meeting.",
        "Vendor sent updated warranty terms for reviewed products.",
        "Vendor requested update on forecasted order volumes.",
        "Vendor provided guidance on product usage and installation.",
        "Vendor requested confirmation on early payment terms.",
        "Vendor sent updated catalog with new product line."
    ]
    return random.choice(notes)


# Function to generate a unique slug for vendor
def generate_unique_slug(vendor_name):
    slug = slugify(vendor_name)
    if Vendor.objects.filter(slug=slug).exists():
        slug = f"{slug}-{random.randint(1000, 9999)}"
    return slug

def generate_unique_code():
    while True:
        code = f"VEND{random.randint(1000, 9999)}"
        if not Vendor.objects.filter(code=code).exists():
            return code

def make_valid_email_domain(vendor_name):
    return re.sub(r'[^a-z0-9-]', '', vendor_name.lower().replace(' ', ''))

def generate_indian_phone_number():
    start_digit = random.choice(['6', '7', '8', '9'])
    remaining_digits = ''.join([str(random.randint(0, 9)) for _ in range(9)])
    phone_number = f"{start_digit}{remaining_digits}"
    phone_pattern = re.compile(r'^[6789]\d{9}$')
    if not phone_pattern.match(phone_number):
        raise ValidationError(f"Invalid phone number format: {phone_number}")
    return phone_number

def generate_address():
    house_number = f"{random.randint(1, 1000)}"
    street_names = ['Main St', 'MG Road', 'Park Avenue', 'Green Lane', 'Shivaji Street']
    street_name = random.choice(street_names)
    building_names = ['Sky Tower', 'Maple Heights', 'Golden Palace', 'Rose Villa']
    building_name = random.choice(building_names)
    landmarks = ['Near Bus Stop', 'Opposite Park', 'Next to Mall', 'Near Temple']
    landmark = random.choice(landmarks)
    zipcode = f"{random.randint(110000, 999999)}"
    
    return house_number, street_name, building_name, landmark, zipcode

class Command(BaseCommand):
    help = 'Generate 100 random vendors with realistic details including address and phone numbers'

    def handle(self, *args, **kwargs):
        NUM_VENDORS = 100
        status_choices = [choice[0] for choice in STATUS_CHOICES]

        # Fetch all vendor types from the database
        vendor_types = VendorType.objects.all()

        if not vendor_types:
            print("No Vendor Types found in the database. Please ensure that VendorType records exist.")
            return

        for i in range(1, NUM_VENDORS + 1):
            vendor_name = random.choice(REAL_VENDORS)
            vendor_code = generate_unique_code()
            status = random.choice(status_choices)

            # Check if vendor_name already exists to avoid duplicates
            if Vendor.objects.filter(company_name1=vendor_name).exists():
                print(f"Vendor with name {vendor_name} already exists.")
                continue

            # Generate a unique slug
            vendor_slug = generate_unique_slug(vendor_name)

            # Randomly choose a VendorType from the existing records
            vendor_type = random.choice(vendor_types)

            # Additional Vendor Details
            payment_terms = random.choice(['Net 7', 'Net 10', 'Net 30', 'Net 60', 'Net 90'])
            
            # Define email and website
            website = f"www.{vendor_name.lower().replace(' ', '')}{random.randint(1, 100)}.com"
            email_1 = f"contact{i}@{make_valid_email_domain(vendor_name)}.com"
            email_2 = f"info{i}@{make_valid_email_domain(vendor_name)}.com"
            email_3 = f"support{i}@{make_valid_email_domain(vendor_name)}.com"

            # Generate phone numbers
            phone_number_1 = generate_indian_phone_number()
            phone_number_2 = generate_indian_phone_number()
            phone_number_3 = generate_indian_phone_number()

            # Generate address
            house_number, street_name, building_name, landmark, zipcode = generate_address()

            # Randomly select country, state, and sublocation from the database
            country = Country.objects.filter(id=1).first()
            state = Location.objects.filter(country=country).order_by('?').first() if country else None
            #sublocation = SubLocation.objects.filter(location=state).order_by('?').first() if state else None

            # Create maps URL
            maps_url = f"https://www.google.com/maps?q={house_number}+{street_name}+{zipcode}"
            note = generate_vendor_note()

            # Save vendor data to the database
            Vendor.objects.create(
                company_name1=vendor_name,
                code=vendor_code,
                status=status,
                vendor_type_id=vendor_type.id,  # Correctly pass the ID of the VendorType
                payment_terms=payment_terms,
                slug=vendor_slug,
                email_1=email_1,
                email_2=email_2,
                email_3=email_3,
                website=website,
                phone_number_1=phone_number_1,
                phone_number_2=phone_number_2,
                phone_number_3=phone_number_3,
                house_number=house_number,
                street_name=street_name,
                building_name=building_name,
                landmark=landmark,
                country_id=country.id if country else 1,
                state_id=state.id if state else None,
                #sublocation_id=sublocation.id if sublocation else None,
                language_id = random.choice(Languages.objects.values_list('id', flat=True)) if Languages.objects.exists() else None,
                zipcode=zipcode,
                maps_url=maps_url,
                notes = note,
            )

        self.stdout.write(self.style.SUCCESS(f'Successfully generated {NUM_VENDORS} vendors.'))
