from django.core.management.base import BaseCommand
from catalog.models import (
    Manufacturer, Languages, Brand, ProductType, Category, Product, ProductLinks, ProductGroup
)
from vendor.models import Vendor
from inventory.models import PurchaseOrderStatus,PurchaseOrderType,PurchaseOrderType,PurchaseOrderHeader
from accounts.models import User
import random
from location.models import Country, Location
from datetime import datetime
from accounts.models import User
import pandas as pd 
from datetime import datetime
from django.conf import settings
import os
import traceback


class Command(BaseCommand):

    help = "Insert master data and test products using update_or_create"
    def handle(self, *args, **kwargs):

        file_path = os.path.join(settings.MEDIA_ROOT, 'Inventory_Application_Data.xlsx')
        df = pd.read_excel(file_path,sheet_name='LOCATION')
        
        for index,row in df.iterrows():
            try:
                loc_obj = Location.objects.get(code=row['WERKS'])
                print (loc_obj.name, loc_obj.pk)
                region =  row['REGIO']
                city =  row['ORT01']
                name =  row['NAME1']
                country_code =  row['LAND1']
                if country_code == 'IN':
                    country_obj = Country.objects.get(name__icontains='INDIA')
                else:
                    country_obj = Country.objects.get(name__icontains='USA')
                loc_obj.name=name
                loc_obj.city=city
                loc_obj.region=region
                loc_obj.country = country_obj
                loc_obj.save()
                

            except Exception as e:
                print(str(e))
                traceback.print_exc()