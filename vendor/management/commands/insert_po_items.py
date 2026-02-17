from django.core.management.base import BaseCommand
from catalog.models import (
    Manufacturer, Languages, Brand, ProductType, Category, Product, ProductLinks, ProductGroup
)
from vendor.models import Vendor
from  inventory.models import  PurchaseOrderHeader,PurchaseOrderStatus,PurchaseOrderType,PurchaseOrderType,PurchaseOrderItem
from accounts.models import User
import random
from location.models import Country
from datetime import datetime
from accounts.models import User
import pandas as pd 
from datetime import datetime
from django.conf import settings
import os
import traceback
from location.models import Location, SubLocation
import random

PRODUCT_NAMES = [
        "Pro Max", "Ultra", "Mini", "Eco", "Prime", "Elite", "X", "S", "Plus", "Go", "Neo", "Lite", "Air", "Edge", "One",
            "Vision", "Smart", "Flex", "Core", "Power"
        ]

class Command(BaseCommand):

    help = "Insert master data and test products using update_or_create"
    def handle(self, *args, **kwargs):

        file_path = os.path.join(settings.MEDIA_ROOT, 'Inventory_Application_Data.xlsx')
        df = pd.read_excel(file_path,sheet_name='PO_ITEM')
        categories = list(Category.objects.all())
        product_types = list(ProductType.objects.all())
        brands = list(Brand.objects.all())
        manufacturers = list(Manufacturer.objects.all())
        languages = list(Languages.objects.all())
        countries = list(Country.objects.all())
        product_groups = list(ProductGroup.objects.all())
        PurchaseOrderItem.objects.all().delete()
        #Product.objects.filter(pk__in=[151,152,153,154]).delete()

        for i,row in df.iterrows():
            #print(row)
            print(row['PRICE'])
            #break
            try:
                category = random.choice(categories)
                product_type = random.choice(product_types)
                product_group = random.choice(product_groups)
                brand = random.choice(brands)
                manufacturer = random.choice(manufacturers)
                language = random.choice(languages)
                country = random.choice(countries)
                name = f"{brand.name} {random.choice(PRODUCT_NAMES)} {i}"
                pdata = {
                            'category': category,
                            'product_type': product_type,
                            'brand': brand,
                            'manufacturer': manufacturer,
                            'language': language,
                            'country': country,
                            'product_group':product_group,
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
                # product, created = Product.objects.update_or_create(
                #         name=row['MATNR'].split('-')[1],
                #         code=row['MATNR'].strip(),  # unique key for each product
                #         defaults=pdata
                #     )
                try:
                   product= Product.objects.get(
                        
                       code=row['MATNR'].strip()
                        
                     )
                   print("product:",product)
                except Exception as e:
                    print(str(e))
                    product, created = Product.objects.update_or_create(
                        name=row['MATNR'],
                        code=row['MATNR'].strip(),  # unique key for each product
                        defaults=pdata
                    )
                subloc_obj = random.choice(SubLocation.objects.all())
                po_header = PurchaseOrderHeader.objects.get(code=row['EBELN'])
                product= Product.objects.get(
                        
                       code=row['MATNR'].strip()
                        
                     )
                po_item_dict = {
                "item":product,
                "po_header":po_header,
                "line_number":row['EBELP'],
                "quantity":row['POQTY'],
                "uom":row['POUOM'],
                "unit_price":row['PRICE'],
                "total_price":row['TOTAL'],
                "item_status":row['ISTAT'],
                "notes":row['ITEXT'],
                "sub_location" : subloc_obj,
                "po_location" : subloc_obj.location,
                "created_user_id" : 2,
                "updated_user_id" : 1,
                "status":1
                }
                po_item, created =PurchaseOrderItem.objects.update_or_create(code=f'{row["EBELN"]}-{i}',defaults=po_item_dict)
                print(po_item,"gggggggggggggg")
            except Exception as e:
                traceback.print_exc()
                print(str(e),"kkkkkkkkkkkkkkkkkkkkkkkk")
