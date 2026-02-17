from django.core.management.base import BaseCommand
from catalog.models import (
    Manufacturer, Languages, Brand, ProductType, Category, Product, ProductLinks, ProductGroup
)
from vendor.models import Vendor
from accounts.models import User
from inventory.models import  PurchaseOrderItem, PurchaseOrderHeader,GoodsMovementHeader,GoodsMovementItem,Inventory,PurchaseOrderHistory
import random
from location.models import Country
from datetime import datetime
from accounts.models import User
import pandas as pd 
from datetime import datetime

import os

class Command(BaseCommand):

    help = "Insert GM Items  using update_or_create"
    def handle(self, *args, **kwargs):
        po_header_code = '2025-00005'
        po_header_list = PurchaseOrderHeader.objects.filter(code=po_header_code)
        po_list  = []
        for po_header in po_header_list:
            po_header_dict = {
            "po_number":po_header.code,
            "vendor":po_header.vendor.company_name1,
            "po_date":po_header.po_date.strftime("%Y%m%d"),
            "po_requested_by":po_header.po_requested_by.username,
            "po_status":po_header.po_status.name,
            "po_type":po_header.po_type.name,
            "requested_delivery_date":po_header.requested_delivery_date.strftime("%Y%m%d"),
            "header_notes":po_header.header_notes,
            "created_user":po_header.created_user.username,
            "updated_user":po_header.updated_user.username,
            "created_at":po_header.created_at.strftime("%Y%m%d"),
            "created_time":po_header.created_at.strftime("%H:%M:%S"),
            "updated_at":po_header.updated_at.strftime("%Y%m%d"),
            "updated_time":po_header.updated_at.strftime("%H:%M:%S")
            }
            print("po_header_dict:",po_header_dict)
            po_list.append(po_header_dict)
        df = pd.DataFrame(po_list)
        df.to_csv('po_header_list.csv',index=False)

        #po line item

        po_item_list = PurchaseOrderItem.objects.filter(po_header__code=po_header_code)

        po_item_rp_list = []
        po_item_matrial =''
        for po_item in po_item_list:
            po_item_matrial = po_item.item.name
            po_item_dict = {
            "po_number":po_item.po_header.code,
            "line_number":po_item.line_number,
            "product":po_item.item.name,
            "quantity":float(po_item.quantity),
            "unit_of_measure":po_item.uom,
            "unit_price":float(po_item.unit_price),
            "total_price":float(po_item.total_price),
            "already_received_qty":float(po_item.already_received_qty),
            "qty_being_received":float(po_item.qty_being_received),
            "yet_to_be_received_qty":float(po_item.yet_to_be_received_qty),
            "item_status":po_item.item_status,
            "notes":po_item.notes,
            "location":po_item.po_location.name,
            "sublocation":po_item.sub_location.name,
            "created_user":po_item.created_user.username,
            "updated_user":po_item.updated_user.username,
            "created_at":po_item.created_at.strftime("%Y%m%d"),
            "created_time":po_item.created_at.strftime("%H:%M:%S"),
            "updated_at":po_item.updated_at.strftime("%Y%m%d"),
            "updated_time":po_item.updated_at.strftime("%H:%M:%S")
            }
            print(po_item_dict)
            po_item_rp_list.append(po_item_dict)
        po_item_df = pd.DataFrame(po_item_rp_list)

        po_item_df.to_csv("po_line_item.csv",index=False)

        #GM Header

        gm_header_list = GoodsMovementHeader.objects.filter(po_header__code=po_header_code)
        gm_header_rp_list = []
        for gm_header in gm_header_list:
            gm_header_dict = {
            "GM Document":gm_header.code,
            "GM Category":gm_header.category,
            "GM Date":gm_header.gm_date.strftime("%Y%m%d"),
            "Posting Date":gm_header.gm_posting_date.strftime("%Y%m%d"),
            "GM Reference":f"PO_{gm_header.po_header.code}",
            "GM Text":gm_header.description,
            "created_user":gm_header.created_user.username,
            "updated_user":gm_header.updated_user.username,
            "created_at":gm_header.created_at.strftime("%Y%m%d"),
            "created_time":gm_header.created_at.strftime("%H:%M:%S"),
            "updated_at":gm_header.updated_at.strftime("%Y%m%d"),
            "updated_time":gm_header.updated_at.strftime("%H:%M:%S")
            }
            gm_header_rp_list.append(gm_header_dict)
        gm_item_list = GoodsMovementItem.objects.filter(document_number__po_header__code=po_header_code)
        gm_item_rp_list = []
        for gm_item in gm_item_list:
            gm_item_dict = {
            "GM Document Number":gm_item.code,
            "GM Item Number":gm_item.item_number,
            "Material Number":gm_item.product.code,
            "Location":gm_item.location.name,
            "SubLocation":gm_item.sub_location.name,
            "GM Quantity":gm_item.quantity,
            "MB Unit of Measure":gm_item.uom,
            "PO Number":gm_item.document_number.po_header.code,
            "PO Line Item Number":gm_item.document_number.po_item.code,
            "GM Type":gm_item.gm_type,
            "GM Item Text":gm_item.gm_item_text,
            "created_user":gm_item.created_user.username,
            "updated_user":gm_item.updated_user.username,
            "created_at":gm_item.created_at.strftime("%Y%m%d"),
            "created_time":gm_item.created_at.strftime("%H:%M:%S"),
            "updated_at":gm_item.updated_at.strftime("%Y%m%d"),
            "updated_time":gm_item.updated_at.strftime("%H:%M:%S")
            }
            gm_item_rp_list.append(gm_item_dict)

        #PO History
        po_history_list = PurchaseOrderHistory.objects.filter(po_header__code=po_header_code)

        po_history_rp_list = []
        for po_history in po_history_list:
            po_history_dict = {
            "PO Number":po_history.po_header.code,
            "PO Line Item Number":po_history.product.code,
            "PO History Number":po_history.po_history_number,
            "PO History Type":po_history.po_history_type,
            "PO History Description":po_history.description,
            "PO Reference Number":f"GM_{po_history.gm_header.code}",
            "PO History Date":po_history.po_history_date.strftime("%Y%m%d"),
            "PO Quantity":po_history.po_quantity,
            "PO Line Amount":po_history.po_line_amount,
            "PO Unit of Measure":po_history.uom,
            "created_user":po_history.created_user.username,
            "updated_user":po_history.updated_user.username,
            "created_at":po_history.created_at.strftime("%Y%m%d"),
            "created_time":po_history.created_at.strftime("%H:%M:%S"),
            "updated_at":po_history.updated_at.strftime("%Y%m%d"),
            "updated_time":po_history.updated_at.strftime("%H:%M:%S")

            }
            po_history_rp_list.append(po_history_dict)



        #Inventory
        po_item_code = [po.item.code for po in po_item_list]
        print("po_item_code:",po_item_code)
        inventory_list =  Inventory.objects.filter(product__code__in=po_item_code)
        inventory_rp_list=[]

        for inv in inventory_list:
            inv_dict = {
            "Material Number":inv.product.code,
            "Location":inv.location.code,
            "SubLocation":inv.sub_location.code,
            "Inventory Type":inv.inventory_type,
            "Inventory Quantity":inv.quantity,
            "Inventory Unit of Measure":inv.uom,

            "created_user":inv.created_user.username,
            "updated_user":inv.updated_user.username,
            "created_at":inv.created_at.strftime("%Y%m%d"),
            "created_time":inv.created_at.strftime("%H:%M:%S"),
            "updated_at":inv.updated_at.strftime("%Y%m%d"),
            "updated_time":inv.updated_at.strftime("%H:%M:%S")
            }
            inventory_rp_list.append(inv_dict)
        print("po_item_matrial:",po_item_matrial)            
        print(inventory_rp_list)
        # import sys
        # sys.exit()
        out_file_path = r"C:\Users\rathn\Documents\Meslova\MeslovaInventoryApp\Inventory_app_data_2025_0005.xlsx"
        os.makedirs(os.path.dirname(out_file_path), exist_ok=True)
        with pd.ExcelWriter(out_file_path, engine="openpyxl") as writer:
            if po_list:
                pd.DataFrame(po_list).to_excel(writer, sheet_name="PO_HEADER", index=False)
            if po_item_rp_list:
                pd.DataFrame(po_item_rp_list).to_excel(writer, sheet_name="PO_ITEM", index=False)
            if gm_header_rp_list:
                pd.DataFrame(gm_header_rp_list).to_excel(writer, sheet_name="GM_HEADER", index=False)
            if gm_item_rp_list:
                pd.DataFrame(gm_item_rp_list).to_excel(writer, sheet_name="GM_ITEM", index=False)
            if po_history_rp_list:
                pd.DataFrame(po_history_rp_list).to_excel(writer, sheet_name="PO_HISTORY", index=False)
            if inventory_rp_list:
                pd.DataFrame(inventory_rp_list).to_excel(writer, sheet_name="INVENTORY", index=False)






