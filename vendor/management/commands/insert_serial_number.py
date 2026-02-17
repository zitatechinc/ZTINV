from django.core.management.base import BaseCommand
from catalog.models import (
    Manufacturer, Languages, Brand, ProductType,
    Category, Product, ProductLinks, ProductGroup
)
from vendor.models import (
    PurchaseOrderHeader, Vendor, PurchaseOrderStatus, PurchaseOrderType,
    GoodsMovementHeader, SerialNumber, GoodsMovementItem, PurchaseOrderItem
)
from accounts.models import User
from location.models import Country
import pandas as pd
from datetime import datetime


class Command(BaseCommand):
    help = "Insert serial numbers from Excel into SerialNumber table using update_or_create"

    def handle(self, *args, **kwargs):
        file_path = r"C:\Users\rathn\Downloads\Inventory_Application_Data.xlsx"
        sheet_name = "SERIAL_NUMBER"

        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to read Excel file: {e}"))
            return

        for _, row in df.iterrows():
            try:
                # --- Product ---
                try:
                    product = Product.objects.get(code=str(row["MATNR"]).strip())
                except Product.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"⚠️ Product not found: {row['MATNR']}"))
                    product = None

                # --- Purchase Order Header ---
                try:
                    po_number = PurchaseOrderHeader.objects.get(code=str(row["EBELN"]).strip())
                except PurchaseOrderHeader.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"⚠️ PO not found: {row['EBELN']}"))
                    po_number = None

                # --- Purchase Order Item ---
                po_item_number = None
                if product and po_number:
                    po_item_code = f"{row['EBELP']}_{product.code}_{po_number.code}"
                    try:
                        po_item_number = PurchaseOrderItem.objects.get(code=po_item_code)
                    except PurchaseOrderItem.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"⚠️ PO Item not found: {po_item_code}"))

                # --- Goods Movement Header ---
                try:
                    gm_document_number = GoodsMovementHeader.objects.get(code=str(row["MBLNR"]).strip())
                except GoodsMovementHeader.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"⚠️ GM Header not found: {row['MBLNR']}"))
                    gm_document_number = None

                # --- Goods Movement Item ---
                gm_item_number = None
                if gm_document_number:
                    try:
                        gm_item_number = GoodsMovementItem.objects.get(code=gm_document_number.code)
                    except GoodsMovementItem.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"⚠️ GM Item not found for GM Header: {gm_document_number.code}"))

                # --- Insert / Update Serial Number ---
                if product and po_number and po_item_number and gm_document_number and gm_item_number:
                    serial_dict = {
                        "material_number": product,
                        "location": str(row["WERKS"]).strip(),
                        "sublocation": str(row["LGORT"]).strip(),
                        "po_number": po_number,
                        "po_line_item_number": po_item_number,
                        "gm_document_number": gm_document_number,
                        "gm_item_number": gm_item_number,
                        "serial_status": str(row["SSTAT"]).strip() if "SSTAT" in row else "",
                    }

                    SerialNumber.objects.update_or_create(
                        code=str(row["SERNR"]).strip(),
                        defaults=serial_dict
                    )

                    self.stdout.write(self.style.SUCCESS(f"✅ Serial Number {row['SERNR']} inserted/updated."))
                else:
                    self.stdout.write(self.style.WARNING(
                        f"⚠️ Skipped Serial {row['SERNR']} - missing dependencies "
                        f"(PO: {po_number}, POItem: {po_item_number}, GMHeader: {gm_document_number}, GMItem: {gm_item_number})"
                    ))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error processing row {row.to_dict()}: {e}"))
