from django.core.management.base import BaseCommand
from catalog.models import (
    Manufacturer, Languages, Brand, ProductType, Category, Product, ProductLinks, ProductGroup
)
from vendor.models import Vendor
from accounts.models import User
from inventory.models import  PurchaseOrderItem, PurchaseOrderHeader
import random
from location.models import Country
from datetime import datetime
from accounts.models import User
import pandas as pd 
from datetime import datetime



class Command(BaseCommand):

    help = "Insert GM Items  using update_or_create"
    def handle(self, *args, **kwargs):
        PurchaseOrderItem.objects.all().delete()
        PurchaseOrderHeader.objects.all().delete()
        # po_item = PurchaseOrderItem.objects.get(pk=1)
        # po_header = po_item.po_header

        # try:
        #     gm_item = process_po_goods_movement(
        #         po_item=po_item,
        #         po_header=po_header,
        #         gm_date=date.today(),
        #         gm_quantity=10,
        #         gm_type="Goods Receipt",
        #         location=po_item.po_location,
        #         sub_location=po_item.sub_location,
        #         gm_text="Received partial shipment",
        #         user=request.user
        #     )
        #     print(f"Goods Movement Item created: {gm_item.code}")
        # except ValidationError as e:
        #     print(f"Failed to process GM: {e}")
