from django.core.management.base import BaseCommand
from catalog.models import (
    Manufacturer, Languages, Brand, ProductType, Category, Product, ProductLinks, ProductGroup
)
from vendor.models import Vendor
from inventory.models import PurchaseOrderStatus,PurchaseOrderType,PurchaseOrderType,PurchaseOrderHeader
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


class Command(BaseCommand):

    help = "Insert master data and test products using update_or_create"
    def handle(self, *args, **kwargs):

        file_path = os.path.join(settings.MEDIA_ROOT, 'Inventory_Application_Data.xlsx')
        df = pd.read_excel(file_path,sheet_name='PO_HEADER')
        
        for index,row in df.iterrows():
            print(row)
            po_number = row.PONumber
            vendor_cls = Vendor.objects.filter(company_name1__icontains=row.VendorNumber).first()
            po_date = row.PODate
            req_delivery_date = row['Requested Delivery Date']
            po_type = PurchaseOrderType.objects.filter(name=row.POType).first()
            po_status = PurchaseOrderStatus.objects.filter(name=row.POStatus).first()
            print (row.RequestedBy)
            RequestedBy =  User.objects.filter(username__icontains=row.RequestedBy.lower().split('.')[0]).first()
            print (RequestedBy)
            
            header_notes = row['HeaderNotes']

            print (po_number, vendor_cls, po_date, RequestedBy, po_status, po_type, req_delivery_date, header_notes)


           
            try:
                
                
                


                po_header_dict = {
                "code": po_number,
                "vendor_id":vendor_cls.pk,
                "po_date":po_date,
                "po_requested_by":RequestedBy,
                "po_status":po_status,
                "requested_delivery_date":req_delivery_date,
                "header_notes":header_notes,
                'po_type':po_type,
                "status":1,
                "created_user_id" : 2,
                "updated_user_id" : 1,
                }
                print (po_header_dict)
                PurchaseOrderHeader.objects.update_or_create(**po_header_dict)
            except Exception as e:
                print(str(e))
                traceback.print_exc()
        for each in PurchaseOrderHeader.objects.all():
            print (each)

            

            
