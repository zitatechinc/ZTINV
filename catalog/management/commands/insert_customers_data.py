import random
import re
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from customer.models import Customer  # Assuming you have a Customer model defined
from catalog.models import Languages  # Assuming you have a Languages model
from location.models import Country, Location, SubLocation
from django.utils.text import slugify
import random

# Real-world company names
REAL_COMPANIES = [
    "Apple Inc.", "Samsung Electronics", "Microsoft Corporation", "Google LLC", 
    "Amazon.com, Inc.", "Tesla, Inc.", "Sony Corporation", "Facebook, Inc.",
    "Netflix, Inc.", "Adobe Systems", "Intel Corporation", "Boeing",
    "Alibaba Group", "Oracle Corporation", "Huawei Technologies", "Walmart Inc.",
    "NVIDIA Corporation", "IBM", "Cisco Systems", "AT&T", "PepsiCo",
    "Nike, Inc.", "Coca-Cola Company", "Starbucks Corporation", "Toyota Motor Corporation",
    "Volkswagen Group", "ExxonMobil", "Johnson & Johnson", "Unilever", 
    "General Electric", "Disney", "McDonald's Corporation", "Ford Motor Company", 
    "Airbus", "Lockheed Martin", "3M", "Siemens", "Pfizer", "Procter & Gamble",
    "Visa Inc.", "MasterCard", "American Express", "L'Oréal", "Dell Technologies",
    "HP Inc.", "Dell Technologies", "BASF", "KPMG", "Accenture", "PwC",
    "Etsy", "Spotify", "Snap Inc.", "Uber Technologies", "Lyft", "Square Inc.", 
    "Zoom Video Communications", "Snapchat", "TikTok", "Slack Technologies",
    "Zoom Video Communications", "Spotify", "Airbnb", "Pinterest", "Salesforce",
    "Oracle", "Square", "Shopify", "Stripe", "Lyft", "Grubhub", "Pinterest",
    "Dropbox", "GitHub", "Slack", "Hulu", "Snapchat", "Spotify", "Reddit",
    "Yahoo!", "Adobe", "SquareSpace", "Fiverr", "Twitch", "Eventbrite", "WordPress",
    "Wix", "TikTok", "Intel", "RedHat", "VMware", "PayPal", "Shopify", "Coinbase",
    "Robinhood", "LinkedIn", "Spotify", "Airbnb", "Pinterest", "Zendesk", "Domo",
    "Atlassian", "Asana", "HubSpot", "Trello", "Mailchimp", "Zapier", "GitLab",
    "Box", "Braintree", "Klarna", "Cash App", "Stripe", "Plaid", "Square",
    "Squarespace", "Zoom", "Netflix", "Uber", "Lyft", "Lyft", "DoorDash", "Postmates",
    "Instacart", "Wayfair", "Chewy", "Etsy", "ShoeDazzle", "StitchFix", "H&M", "Zara",
    "Lululemon", "Uniqlo", "Skechers", "Adidas", "Reebok", "Under Armour", "Puma", 
    "Vans", "Converse", "Nike", "Lacoste", "New Balance", "Tommy Hilfiger", "Gucci",
    "Louis Vuitton", "Chanel", "Prada", "Hermès", "Fendi", "Burberry", "Versace",
    "Rolex", "Cartier", "Omega", "Tag Heuer", "Tiffany & Co.", "Patek Philippe",
    "Richemont", "Swatch Group", "Chopard", "IWC Schaffhausen", "Montblanc", "Bvlgari",
    "Hublot", "Jaeger-LeCoultre", "Vacheron Constantin", "LVMH", "Kering", "Richemont",
    "Tesla", "Rivian", "Lucid Motors", "Ford", "General Motors", "Toyota", "Honda",
    "BMW", "Mercedes-Benz", "Audi", "Volkswagen", "Hyundai", "Nissan", "Porsche", 
    "Ferrari", "Lamborghini", "McLaren", "Aston Martin", "Bugatti", "Rolls-Royce",
    "Bentley", "Jeep", "Chrysler", "Peugeot", "Fiat", "Tesla", "Cadillac", "Subaru",
    "Mazda", "Land Rover", "Jaguar", "Mitsubishi", "Alfa Romeo", "Volvo", "SAAB",
    "Chrysler", "Chevrolet", "Ford", "Dodge", "Ram Trucks", "GMC", "Jeep", "Buick",
    "Lincoln", "Hyundai", "Kia", "Toyota", "Honda", "Nissan", "Mazda", "Subaru", "BMW",
    "Mercedes-Benz", "Audi", "Volkswagen", "Porsche", "Ferrari", "Lamborghini", "McLaren"
]


STATUS_CHOICES = [
    (-1, "Inactive"),
    (0, "Draft"),
    (1, "Active"),
]


def generate_note():
    notes = [
        "Customer is exploring additional product options.",
        "Frequent buyer with excellent payment history.",
        "Customer experiencing technical issues with products.",
        "Requested product catalog for review.",
        "Customer inquired about upcoming promotions.",
        "Customer prefers to deal with a specific account manager.",
        "Client has signed up for our loyalty program.",
        "Customer is a new lead, needs onboarding.",
        "Customer is interested in upgrading their service plan.",
        "Client is looking for faster response times.",
        "Customer reports a defect in recently purchased items.",
        "Customer has requested detailed product specifications.",
        "Customer inquired about our return policy.",
        "Customer is a seasonal buyer, orders during sales.",
        "Client needs a copy of their last invoice.",
        "Customer wants to negotiate bulk order pricing.",
        "Customer prefers in-person meetings for important issues.",
        "Client is waiting for an official quote to proceed.",
        "Customer has requested a custom quote for long-term service.",
        "Client recently added more locations for distribution.",
        "Customer has given a recommendation for a referral program.",
        "Customer is experiencing a delay in shipping.",
        "Customer recently relocated their business operations.",
        "Client is interested in exploring new product categories.",
        "Customer has praised our customer support team.",
        "Customer has reported a billing issue.",
        "Client regularly orders high-value items.",
        "Customer is interested in a trial period for services.",
        "Customer inquired about our shipping partners.",
        "Client has requested additional stock for their stores.",
        "Customer wants updates on product availability.",
        "Client needs assistance with installation services.",
        "Customer has expressed interest in a partnership.",
        "Client has requested a service upgrade.",
        "Customer prefers to buy in larger quantities.",
        "Customer frequently orders custom-tailored solutions.",
        "Client asked for clarification on product features.",
        "Customer has referred multiple clients to our business.",
        "Client has requested a demo on site.",
        "Customer would like to discuss long-term contract terms.",
        "Customer expressed satisfaction with the recent purchase.",
        "Customer would like to be notified of future product releases.",
        "Customer has asked for additional payment options.",
        "Customer is interested in collaborating on a promotional campaign.",
        "Client needs assistance with installation of purchased products.",
        "Customer frequently requests technical support.",
        "Customer is a distributor of our products in their region.",
        "Client asked for expedited processing of their order.",
        "Customer requested information on the latest upgrades.",
        "Customer has requested a detailed comparison of products.",
        "Client has a preferred shipping carrier for all orders.",
        "Customer has an upcoming event and requested a product order.",
        "Customer frequently orders in large quantities.",
        "Client has requested a special discount code.",
        "Customer is asking for updates on delivery schedules.",
        "Customer needs a follow-up on their recent complaint.",
        "Client inquired about corporate social responsibility efforts.",
        "Customer asked for details on custom packaging options.",
        "Client requested a free trial for one of our products.",
        "Customer asked about the status of their warranty claim.",
        "Customer requested information about our return process.",
        "Customer needs clarification on product safety features.",
        "Customer has recently changed their contact details.",
        "Customer has had a recent issue with their account.",
        "Customer is looking for a solution to streamline their processes.",
        "Customer needs assistance with setting up their new account.",
        "Client has requested a meeting to review their contract terms.",
        "Customer frequently orders through our online store.",
        "Client has a special request regarding their upcoming order.",
        "Customer inquired about the most popular products in their industry.",
        "Customer is a VIP client with top-tier service requirements.",
        "Customer is interested in setting up a recurring order.",
        "Client needs help choosing the right product for their needs.",
        "Customer has asked about future product launches.",
        "Customer has shared positive feedback about their recent purchase.",
        "Client has requested expedited delivery on all future orders.",
        "Customer has made a complaint regarding product packaging.",
        "Customer needs to update their billing information.",
        "Client has requested a detailed proposal for a partnership.",
        "Customer is looking for more environmentally friendly options.",
        "Client has inquired about customizing their product order.",
        "Customer is a high-value client, needs priority service.",
        "Customer is asking for a summary of their recent transactions.",
        "Client has requested additional marketing materials.",
        "Customer requested an update on backordered items.",
        "Client is considering expanding their order this quarter.",
        "Customer is interested in testing a new product feature.",
        "Client frequently purchases seasonal items in bulk.",
        "Customer has asked for details on our product guarantees.",
        "Customer is awaiting an update on their order status.",
        "Client needs to confirm the shipping address for their next order.",
        "Customer needs further details on available support options.",
        "Client has requested a customized product solution.",
        "Customer is interested in our extended warranty program.",
        "Customer is looking for an upgrade to a more premium service package.",
        "Client has asked for our latest product catalog.",
        "Customer is a loyal customer, always pays on time.",
        "Customer is experiencing some delays with their recent orders.",
        "Client frequently requests updates on product availability.",
        "Customer would like to see more promotions for loyal customers.",
        "Client has requested a customer satisfaction survey."
    ]
    return random.choice(notes)

# Function to generate a unique slug
def generate_unique_slug(company_name1):
    slug = slugify(company_name1)
    # Check if the slug already exists in the database
    if Customer.objects.filter(slug=slug).exists():
        # Add a unique suffix if the slug already exists
        slug = f"{slug}-{random.randint(1000, 9999)}"
    return slug

def generate_unique_code():
    while True:
        # Generate a random code
        code = f"CUST{random.randint(1000, 9999)}"
        # Check if the code already exists in the database
        if not Customer.objects.filter(code=code).exists():
            return code

# Helper function to generate valid email domains
def make_valid_email_domain(company_name):
    # Remove invalid characters (like commas, periods) from the company name for email domain
    return re.sub(r'[^a-z0-9-]', '', company_name.lower().replace(' ', ''))

# Helper function to generate valid Indian phone numbers (starting with 6, 7, 8, or 9)
def generate_indian_phone_number():
    # Start with 6, 7, 8, or 9
    start_digit = random.choice(['6', '7', '8', '9'])
    # Generate the remaining 9 digits
    remaining_digits = ''.join([str(random.randint(0, 9)) for _ in range(9)])
    # Combine them to form a 10-digit phone number
    phone_number = f"{start_digit}{remaining_digits}"
    # Validate with regex pattern for a valid 10-digit Indian mobile number
    phone_pattern = re.compile(r'^[6789]\d{9}$')
    if not phone_pattern.match(phone_number):
        raise ValidationError(f"Invalid phone number format: {phone_number}")
    
    return phone_number


# Helper function to generate valid Indian fax numbers (using typical area codes for major cities)
def generate_indian_fax_number():
    # List of some common area codes in India
    area_codes = ['011', '022', '033', '044', '080', '0124', '040', '079', '098', '020']
    # Choose a random area code from the list
    area_code = random.choice(area_codes)
    # Generate the remaining 7 digits for the fax number
    remaining_digits = ''.join([str(random.randint(0, 9)) for _ in range(7)])
    # Combine the area code and remaining digits
    fax_number = f"+91-{area_code}-{remaining_digits}"
    # Validate with regex pattern for a valid Indian fax number format
    fax_pattern = re.compile(r'^\+91-\d{3,4}-\d{7,8}$')
    if not fax_pattern.match(fax_number):
        raise ValidationError(f"Invalid fax number format: {fax_number}")
    
    return fax_number


# Helper function to generate random address data
def generate_address():
    # Random house number
    house_number = f"{random.randint(1, 1000)}"
    # Random street name (using a few predefined names)
    street_names = [
    'Main St', 'MG Road', 'Park Avenue', 'East End', 'Green Lane', 'Shivaji Street',
    'Bengaluru Road', 'Andheri West', 'Cunningham Road', 'Nehru Place', 'Worli Sea Face',
    'Bandra Kurla Complex', 'Chandni Chowk', 'Janpath', 'Connaught Place', 'Vasant Vihar',
    'Hauz Khas', 'South Extension', 'Kochi Bypass', 'Raja Street', 'Gandhi Nagar', 'Mahatma Gandhi Road',
    'Vivekananda Road', 'Bapuji Nagar', 'Cuffe Parade', 'Lajpat Nagar', 'Sector 15', 'Jammu Road',
    'Ballygunge Circular Road', 'Thakur Village', 'Nungambakkam', 'Chennai Road', 'Frazer Town', 'Vaishali Nagar',
    'Shalimar Bagh', 'Bihar Sharif Road', 'Santacruz East', 'Kolkata Road', 'Lower Parel', 'Kalamboli', 
    'Jayanagar', 'Indiranagar', 'Hinjewadi', 'Pune-Mumbai Road', 'Sadar Bazar', 'R S Road', 'Anna Nagar']

    street_name = random.choice(street_names)
    # Random building name (optional, some customers might not have this)
    building_names = [
    'Sky Tower', 'Maple Heights', 'Golden Palace', 'Rose Villa', 'Silver Oak',
    'Blueberry Heights', 'Palm Grove', 'Emerald Tower', 'Sunshine Apartments', 'Royal Residency',
    'Anand Mansion', 'Pragati Tower', 'Sapphire Heights', 'Lotus Park', 'Elite Tower', 'Harbour View',
    'Pearl Residency', 'Shivam Towers', 'Silver Birch', 'Ritz Royale', 'Opal Gardens', 'Victoria Tower',
    'Crystal Palace', 'Sunset Apartments', 'Breezeway Towers', 'New Horizons Building', 'The Grand Hive',
    'Uptown Residency', 'Urban Palms', 'Redwood Towers', 'Mountview Residency', 'Luxury Heights',
    'Golden Crest', 'Lush Heights', 'Seaview Estate', 'Vantage Point', 'Tranquil Heights', 'Hillcrest Manor',
    'The Prestige', 'The Serenity', 'The Lotus Garden', 'Indigo Tower', 'Arista Heights']

    building_name = random.choice(building_names)
    
    # Random landmark (optional, some customers might not have this)
    landmarks = [
    'Near Bus Stop', 'Opposite Park', 'Next to Mall', 'Near Temple', 'Behind School',
    'Near Railway Station', 'Close to Airport', 'Opposite Metro Station', 'Near Water Tank',
    'Adjacent to Hospital', 'Next to Market', 'Behind Petrol Pump', 'Near Police Station',
    'Close to IT Park', 'Opposite Cinema Hall', 'Near Shopping Complex', 'Near Post Office',
    'Beside Metro Station', 'Close to Stadium', 'Behind Hotel', 'Near Fire Station',
    'Near Church', 'Opposite Mall', 'Near Government Office', 'Close to Restaurant',
    'Near School Gate', 'Beside Big Bazaar', 'Near Government Hospital', 'Close to Bus Depot',
    'Near Botanical Garden', 'Opposite College', 'Close to Bank', 'Near ATM', 'Beside Temple',
    'Near College Entrance', 'Close to Market Square', 'Near Gas Station', 'Opposite Hotel',
    'Behind Railway Station', 'Next to Bakery', 'Beside Sports Complex', 'Near College Ground',
    'Near Police Chowki', 'Close to Red Light', 'Near Village Market', 'Near Community Hall',
    'Opposite Shopping Mall', 'Near National Park', 'Near Sadar Bazar', 'Close to College Hostel',
    'Near Panchayat Office', 'Close to Water Fountain', 'Near High Court', 'Behind School Playground',
    'Next to Supermarket', 'Beside the Bridge', 'Near the Lake', 'Opposite the Beach',
    'Close to City Center', 'Near the Bus Terminal']


    landmark = random.choice(landmarks)
    
    # Random Zipcode (assuming Indian pin codes)
    zipcode = f"{random.randint(110000, 999999)}"
    
    return house_number, street_name, building_name, landmark, zipcode


# Create the custom management command class
class Command(BaseCommand):
    help = 'Generate 100 random customers with realistic details including address and fax numbers'

    def handle(self, *args, **kwargs):
        # Number of customers to generate
        NUM_CUSTOMERS = 100
        status_choices = [choice[0] for choice in STATUS_CHOICES]

        for i in range(1, NUM_CUSTOMERS + 1):
            company_name1 = random.choice(REAL_COMPANIES)
            company_name2 = f"{company_name1} Corp" if i % 2 == 0 else ""
            customer_code = generate_unique_code()
            status = random.choice(status_choices)

            # Check if company_name1 already exists in the database to avoid duplicates
            if Customer.objects.filter(company_name1=company_name1).exists():
                print(f"Customer with company name {company_name1} already exists.")
                continue  # Skip creating this customer if it exists
            # Generate a unique slug
            customer_slug = generate_unique_slug(company_name1)

            customer_type = random.choice(['Retail Customer', 'Wholesale Customer','Corporate Customer','Government Customer','Online Customer','Walk-in Customer','Internal Customer']) 
            dba = f"DBA {i}" if i % 3 == 0 else ""
            payment_terms = random.choice(['Net 7', 'Net 10', 'Net 30', 'Net 60', 'Net 90'])
            
            # Define email and website before using them in search_keywords
            website = f"www.{company_name1.lower().replace(' ', '')}{random.randint(1, 100)}.com"
            # Generate emails with valid domains
            email_1 = f"contact{i}@{make_valid_email_domain(company_name1)}.com"
            email_2 = f"info{i}@{make_valid_email_domain(company_name1)}.com"
            email_3 = f"support{i}@{make_valid_email_domain(company_name1)}.com"
            search_keywords = f"{company_name1}, {customer_type}, {customer_code}, {website}, {email_1}, {email_2}, {email_3}"

            phone_number_1 = generate_indian_phone_number()
            phone_number_2 = generate_indian_phone_number()
            phone_number_3 = generate_indian_phone_number()
            fax_number = generate_indian_fax_number()

            # Generate address data
            house_number, street_name, building_name, landmark, zipcode = generate_address()

            # Randomly select country, state, and sublocation from the database
            country = Country.objects.filter(id=1).first()  # Always select country with id=1
            state = Location.objects.filter(country=country).order_by('?').first() if country else None
            sublocation = SubLocation.objects.filter(location=state).order_by('?').first() if state else None

            # Generate a random Google Maps URL (you can modify this pattern as needed)
            maps_url = f"https://www.google.com/maps?q={house_number}+{street_name}+{zipcode}"
            note = generate_note()

            # Save customer data to the database
            Customer.objects.create(
                company_name1=company_name1,
                company_name2=company_name2,
                code=customer_code,
                status=status,

                customer_type=customer_type,
                dba=dba,
                payment_terms=payment_terms,

                slug=customer_slug,
                language_id = random.choice(Languages.objects.values_list('id', flat=True)) if Languages.objects.exists() else None,
                search_keywords=search_keywords,
                
                phone_number_1=phone_number_1,
                phone_number_2=phone_number_2,
                phone_number_3=phone_number_3,
                fax=fax_number,  

                email_1=email_1,
                email_2=email_2,
                email_3=email_3,
                website=website,
                
                house_number=house_number,
                street_name=street_name,
                building_name=building_name,
                landmark=landmark,

                country_id=country.id if country else 1,
                state_id=state.id if state else None,
                sublocation_id=sublocation.id if sublocation else None,
                zipcode=zipcode,
                maps_url=maps_url,
                notes = note
            )

        self.stdout.write(self.style.SUCCESS(f'Successfully generated {NUM_CUSTOMERS} customers with phone numbers, addresses, and fax numbers.'))
