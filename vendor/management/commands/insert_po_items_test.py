from django.core.management.base import BaseCommand
from catalog.models import (
    Manufacturer, Languages, Brand, ProductType, Category, Product, ProductLinks, ProductGroup
)
from vendor.models import PurchaseOrderHeader,Vendor,PurchaseOrderStatus,PurchaseOrderType,PurchaseOrderType,PurchaseOrderItem
from accounts.models import User
import random
from location.models import Country
from datetime import datetime
from accounts.models import User
import pandas as pd 
from datetime import datetime

PRODUCT_NAMES = [
        "Pro Max", "Ultra", "Mini", "Eco", "Prime", "Elite", "X", "S", "Plus", "Go", "Neo", "Lite", "Air", "Edge", "One",
            "Vision", "Smart", "Flex", "Core", "Power"
        ]

class Command(BaseCommand):

    help = "Insert master data and test products using update_or_create"
    def handle(self, *args, **kwargs):
        code_list =[]
        df = pd.read_excel(r'C:\Users\rathn\Downloads\Inventory_Application_Data.xlsx',sheet_name='PO_ITEM')
        for i,row in df.iterrows():
            code_list.append(f'{row["EBELN"]}_{row["EBELP"]}_{row['MATNR']}')
        print(len(list(set(code_list))))            