from django.core.management.base import BaseCommand
from catalog.models import (
    Manufacturer, Languages, Brand, ProductType, Category, Product, ProductLinks, ProductGroup
)
from vendor.models import PurchaseOrderHeader,Vendor,PurchaseOrderStatus,PurchaseOrderType,PurchaseOrderType,GoodsMovementHeader,GoodsMovementItem,PurchaseOrderItem,PurchaseOrderHistory
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

        df = pd.read_excel(r'C:\Users\rathn\Downloads\Inventory_Application_Data.xlsx',sheet_name='PO_HISTORY')
        
        for index,row in df.iterrows():
            print(row)
            try:

                try:
                    gm_item = GoodsMovementItem.objects.get(code=row['EBREF'].replace('GM-0',''))
                    print("hiiiiiiiiiiiiiii")
                    print(gm_item.material_number)
                except Exception as e:
                    print(str(e))
                    gm_item = None
                try:
                    po_number = PurchaseOrderHeader.objects.get(code=row['EBELN'])
                except Exception as e:
                    print(str(e))
                    po_number = None
                try:
                    po_item = PurchaseOrderItem.objects.get(code=f'{row["EBELP"]}_{gm_item.material_number.code}_{po_number.code}')
                except Exception as e:
                    print(str(e))
                    po_item = None
                if gm_item  and po_number and po_item:
                    po_history_date = datetime.strptime(str(row['EBDAT']), "%Y%m%d").date()
                    poh_item_dict ={
                    
                    "po_number":po_number,
                    "po_line_item_number":po_item,
                    "gm_reference_number":gm_item,
                    "po_quantity":row['EBQTY'],
                    "uom":row['EBUOM'],
                    "po_history_date":po_history_date,
                    "po_quantity":row['EBQTY'],
                    "po_line_amount":row['EBAMT'],
                    "po_history_type":row['EBEVT'],
                    "po_history_number":row['EBHLN']

                    }
                    PurchaseOrderHistory.objects.update_or_create(**poh_item_dict)
                else:
                    print("master references are not there")
            except Exception as e:
                print(str(e))
