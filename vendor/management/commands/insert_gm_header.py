from django.core.management.base import BaseCommand
from catalog.models import (
    Manufacturer, Languages, Brand, ProductType,
    Category, Product, ProductLinks, ProductGroup
)
from vendor.models import (
    PurchaseOrderHeader, Vendor, PurchaseOrderStatus,
    PurchaseOrderType, GoodsMovementHeader
)
from accounts.models import User
from location.models import Country
import pandas as pd
from datetime import datetime


class Command(BaseCommand):
    help = "Insert master data and test products using update_or_create"

    def handle(self, *args, **kwargs):
        file_path = r"C:\Users\rathn\Downloads\Inventory_Application_Data.xlsx"
        sheet_name = "GM_HEADER"

        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to read Excel file: {e}"))
            return

        # Clear existing records
        GoodsMovementHeader.objects.all().delete()
        self.stdout.write(self.style.WARNING("Existing GoodsMovementHeader records deleted."))

        for _, row in df.iterrows():
            try:
                # Convert dates (YYYYMMDD → date)
                gm_date = datetime.strptime(str(row["MBDAT"]), "%Y%m%d").date()
                gm_posting_date = datetime.strptime(str(row["MBPDT"]), "%Y%m%d").date()

                # Clean up reference (remove "PO-" prefix)
                gm_reference_code = str(row["MBREF"]).replace("PO-", "").strip()

                try:
                    gm_reference_obj = PurchaseOrderHeader.objects.get(code=gm_reference_code)
                except PurchaseOrderHeader.DoesNotExist:
                    gm_reference_obj = None

                if gm_reference_obj:
                    gm_dict = {
                        "gm_reference": gm_reference_obj,
                        "category": row["MBCAT"],
                        "gm_date": gm_date,
                        "gm_posting_date": gm_posting_date,
                        "gm_text": str(row["HTEXT"]).strip() if pd.notna(row["HTEXT"]) else "",
                        "status": 1,
                    }

                    GoodsMovementHeader.objects.update_or_create(
                        code=str(row["MBLNR"]).strip(),
                        defaults=gm_dict
                    )
                    self.stdout.write(self.style.SUCCESS(
                        f"Inserted/Updated GM Header: {row['MBLNR']}"
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f"No PO reference found for GM Header: {row['MBLNR']}"
                    ))

            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Error processing row {row.to_dict()}: {e}"
                ))
