from django.core.management.base import BaseCommand
from catalog.models import (
    Manufacturer, Languages, Brand, ProductType, Category, Product, ProductLinks, ProductGroup
)
from vendor.models import PurchaseOrderHeader,Vendor,PurchaseOrderStatus,PurchaseOrderType,PurchaseOrderType,GoodsMovementHeader,GoodsMovementItem,PurchaseOrderItem
from accounts.models import User
import random
from location.models import Country
from datetime import datetime
from accounts.models import User
import pandas as pd 
from datetime import datetime



class Command(BaseCommand):

    help = "Insert GM Items  using update_or_create"
    def handle(self, *args, **kwargs):

        df = pd.read_excel(r'C:\Users\rathn\Downloads\Inventory_Application_Data.xlsx',sheet_name='GM_ITEM')
        
        for index,row in df.iterrows():
            print(row)
            try:

                try:
                    gm_header = GoodsMovementHeader.objects.get(code=row['MBLNR'])
                except Exception as e:
                    print(str(e))
                    gm_header = None
                try:
                    product = Product.objects.get(code=row['MATNR'])
                except Exception as e:
                    print(str(e),row['MATNR'])
                    product = None
                try:
                    po_number = PurchaseOrderHeader.objects.get(code=row['ELEBN'].replace('PO-',''))
                except Exception as e:
                    print(str(e))
                    po_number = None
                try:
                    po_item = PurchaseOrderItem.objects.get(code=f'{row["EBELP"]}_{product.code}_{po_number.code}')
                except Exception as e:
                    print(str(e))
                    po_item = None
                if gm_header and product and po_number and po_item:
                    gm_item_dict ={
                    "document_number":gm_header,
                    "po_number":po_number,
                    
                    "item_number":row['MBLPO'],
                    "material_number":product,
                    "location":row['WERKS'],
                    "sublocation":row['LGORT'],
                    "quantity":row['MBQTY'],
                    "uom":row['MBUOM'],
                    "gm_type":row['MBTYP'],
                    "gm_item_text":row['ITEXT'],
                    }
                    GoodsMovementItem.objects.update_or_create(code=gm_header.code,defaults=gm_item_dict)
                else:
                    print("master references are not there")
            except Exception as e:
                print(str(e))
