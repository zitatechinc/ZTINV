from django.core.management.base import BaseCommand
from location.models import Country
from catalog.models import Languages
from vendor.models import Vendor, VendorBank, VendorTax
import random
from accounts.models import User


class Command(BaseCommand):
    help = "Insert 25 test vendors with related data"

    def handle(self, *args, **kwargs):
        # VendorTax.objects.all().delete()
        # VendorBank.objects.all().delete()
        # Vendor.objects.all().delete()

        user_obj = User.objects.filter(username='admin_user').first()
        # --- Ensure master data exists ---
        country = Country.objects.filter(name__icontains='India').first()
        
        lang= Languages.objects.filter(name='English').first()
        

        # --- 25 Vendors ---
        vendor_data = [
            # Auto/Manufacturing
            {"company_name1": "Tata Motors Ltd", "dba": "Tata", "vendor_type": "Manufacturer"},
            {"company_name1": "Maruti Suzuki India Ltd", "dba": "Maruti", "vendor_type": "Manufacturer"},
            {"company_name1": "Mahindra & Mahindra", "dba": "Mahindra", "vendor_type": "Manufacturer"},
            {"company_name1": "Hyundai India", "dba": "Hyundai", "vendor_type": "Manufacturer"},
            {"company_name1": "Hero MotoCorp", "dba": "Hero", "vendor_type": "Manufacturer"},

            # IT / Services
            {"company_name1": "APPLE", "dba": "Infosys", "vendor_type": "Service Vendor"},
            {"company_name1": "DELL", "dba": "Wipro", "vendor_type": "Service Vendor"},
            {"company_name1": "SAMSUNG", "dba": "TechM", "vendor_type": "Service Vendor"},
            {"company_name1": "LENOVO", "dba": "HCL", "vendor_type": "Service Vendor"},
            # {"company_name1": "TCS", "dba": "TCS", "vendor_type": "Service Vendor"},

            # Retail / Distribution
            {"company_name1": "Reliance Retail Ltd", "dba": "Reliance", "vendor_type": "Distributor"},
            {"company_name1": "Flipkart Internet Pvt Ltd", "dba": "Flipkart", "vendor_type": "Distributor"},
            {"company_name1": "Amazon India Pvt Ltd", "dba": "Amazon", "vendor_type": "Distributor"},
            {"company_name1": "DMart", "dba": "DMart", "vendor_type": "Distributor"},
            {"company_name1": "Spencers Retail", "dba": "Spencers", "vendor_type": "Distributor"},

            # FMCG / Consumer Goods
            {"company_name1": "Hindustan Unilever Ltd", "dba": "Unilever", "vendor_type": "Distributor"},
            {"company_name1": "ITC Limited", "dba": "ITC", "vendor_type": "Distributor"},
            {"company_name1": "Nestle India", "dba": "Nestle", "vendor_type": "Distributor"},
            {"company_name1": "Britannia Industries", "dba": "Britannia", "vendor_type": "Distributor"},
            {"company_name1": "Parle Products", "dba": "Parle", "vendor_type": "Distributor"},

            # Telecom / Infra
            {"company_name1": "Bharti Airtel Ltd", "dba": "Airtel", "vendor_type": "Service Vendor"},
            {"company_name1": "Vodafone Idea Ltd", "dba": "Vi", "vendor_type": "Service Vendor"},
            {"company_name1": "Jio Platforms Ltd", "dba": "Jio", "vendor_type": "Service Vendor"},
            {"company_name1": "BSNL", "dba": "BSNL", "vendor_type": "Service Vendor"},
            {"company_name1": "Adani Enterprises", "dba": "Adani", "vendor_type": "Manufacturer"},
        ]

        for i, data in enumerate(vendor_data, start=1):
            vendor, created = Vendor.objects.update_or_create(
                company_name1=data["company_name1"],
                defaults={
                    "company_name2": data["company_name1"],
                    "dba": data["dba"],
                    "vendor_type": data["vendor_type"],
                    "search_keywords": f"{data['dba'].lower()}, vendor, supplier",
                    "website": f"https://www.{data['dba'].lower()}.com",
                    "notes": f"Auto-generated vendor record {i}",
                    "payment_terms": random.choice(["Net 15", "Net 30", "Net 45", "Advance", "COD"]),
                    "house_number": f"{100+i}",
                    "street_name": "Business Street",
                    "state": random.choice(["Maharashtra", "Karnataka", "Delhi", "Haryana", "Tamil Nadu"]),
                    "zipcode": str(400000 + i),
                    "phone_number_1": f"91{9000000000+i}",
                    "email_1": f"contact{i}@{data['dba'].lower()}.com",
                    "country": country,
                    "language": lang,
                    "created_user":user_obj,
                    "status" : 1,
                    "code" : f"VND-{i+50}"
                },
            )
            self.stdout.write(
                self.style.SUCCESS(f"Vendor {vendor.company_name1} {'created' if created else 'updated'}")
            )

            # --- Vendor Bank ---
            VendorBank.objects.update_or_create(
                vendor=vendor,
                account_number=f"{9000000000+i}",
                defaults={
                    "account_holder_name": vendor.company_name1,
                    "routing_number": f"RT{i:04d}",
                    "account_type": random.choice(["Savings", "Current"]),
                    "bank_name": "State Bank of India",
                    "branch_name": f"Branch {i}",
                    "ifsc_code": f"SBIN000{i:04d}",
                    "micr_code": f"40000{i:03d}",
                    "primary": True,
                    "created_user":user_obj,
                    "status" : 1
                },
            )

            # --- Vendor Tax ---
            VendorTax.objects.update_or_create(
                vendor=vendor,
                tax_number=f"{i:20d}",
                defaults={
                    "name": f"{vendor.company_name1} GST",
                    "category": "GST",
                    "country": country,
                    "tax_rate": random.choice([5.0, 12.0, 18.0]),
                   # "other_tax_details": f"Auto t,est GST for vendor {i}",
                    "created_user":user_obj,
                    "status" : 1
                },
            )

           
