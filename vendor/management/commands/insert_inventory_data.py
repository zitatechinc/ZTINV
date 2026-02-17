from django.core.management.base import BaseCommand
from catalog.models import Product
from vendor.models import Inventory
import pandas as pd


class Command(BaseCommand):
    help = "Insert or update Inventory records from Excel (SERIAL_NUMBER sheet)."

    def handle(self, *args, **kwargs):
        file_path = r"C:\Users\rathn\Downloads\Inventory_Application_Data.xlsx"
        sheet_name = "SERIAL_NUMBER"

        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to read Excel file '{file_path}': {e}"))
            return

        self.stdout.write(self.style.NOTICE(f"📄 Processing {len(df)} rows from '{sheet_name}'..."))

        for _, row in df.iterrows():
            try:
                product_code = str(row.get("MATNR", "")).strip()

                if not product_code:
                    self.stdout.write(self.style.WARNING("⚠️ Skipping row: missing 'MATNR'."))
                    continue

                # --- Product ---
                try:
                    product = Product.objects.get(code=product_code)
                except Product.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"⚠️ Product not found: {product_code}"))
                    continue

                # --- Inventory dict ---
                inventory_data = {
                    "material_number": product,
                    "location": str(row.get("WERKS", "")).strip(),
                    "sublocation": str(row.get("LGORT", "")).strip(),
                    "inventory_type": str(row.get("ITYPE", "")).strip(),
                    "quantity": float(row.get("LBKUM", 0)) if row.get("LBKUM") else 0,
                    "uom": str(row.get("MEINS", "")).strip(),
                }

                obj, created = Inventory.objects.update_or_create(
                    code=product.code,  # assuming `code` is unique key for Inventory
                    defaults=inventory_data,
                )

                status_msg = "✅ Created" if created else "🔄 Updated"
                self.stdout.write(self.style.SUCCESS(f"{status_msg} Inventory for product {product.code}"))

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error processing row {row.to_dict()}: {e}")
                )

        self.stdout.write(self.style.SUCCESS("🎉 Inventory import completed successfully!"))
