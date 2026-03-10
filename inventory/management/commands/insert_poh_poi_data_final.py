# from django.core.management.base import BaseCommand
# from django.db import connections
# from datetime import datetime
# from django.utils import timezone
# from inventory.models import PurchaseOrderStatus, PurchaseOrderHeader, PurchaseOrderItem
# from location.models import SubLocation


# class Command(BaseCommand):
#     help = "Insert PO Header and Items only (no updates)"

#     def handle(self, *args, **kwargs):
#         source_conn = connections['default']
#         source_cursor = source_conn.cursor()

#         destination_conn = connections['default']
#         destination_cursor = destination_conn.cursor()

#         # ------------------------------------------------------------------
#         # QUERY SOURCE DATA
#         # ------------------------------------------------------------------
#         query = """
#         SELECT
#             po.po_number,
#             strftime('%Y-%m-%d %H:%M:%S', po.date_created),
#             dpo.sources_id,
#             dpo_particular.quantity_dpo,
#             dpo_particular.unit_price_dpo,
#             dpo_particular.total_value,
#             subloc.name,
#             p.item_specification,
#             unit.unit,
#             cp.id
#         FROM ims_poapproval AS pa
#         JOIN ims_purchase_order AS po ON pa.po_id = po.id
#         JOIN ims_dpo AS dpo ON po.draft_po_id = dpo.id
#         JOIN ims_procurement AS proce ON dpo.procurement_id = proce.id
#         JOIN location_sublocation AS subloc ON proce.branch_id = subloc.id
#         JOIN ims_dpo_particular AS dpo_dpos ON dpo.id = dpo_dpos.dpo_id
#         JOIN ims_dpoparticular AS dpo_particular ON dpo_dpos.dpoparticular_id = dpo_particular.id
#         JOIN ims_quotationparticular AS qp ON dpo_particular.quotation_particular_id = qp.id
#         JOIN ims_particular AS p ON qp.csparticular_id = p.id
#         JOIN ims_units AS unit ON p.unitname_id = unit.id
#         JOIN catalog_product AS cp ON p.product_id = cp.id
#         WHERE pa.done_sign = 1
#         ORDER BY po.po_number;
#         """

#         source_cursor.execute(query)
#         rows = source_cursor.fetchall()
#         print(f"Fetched {len(rows)} rows")

#         # ------------------------------------------------------------------
#         # CACHES
#         # ------------------------------------------------------------------
#         line_number_cache = {}

#         # ------------------------------------------------------------------
#         # GET STATUS
#         # ------------------------------------------------------------------
#         pos = PurchaseOrderStatus.objects.get(name='OPEN')

#         try:
#             for row in rows:
#                 po_number = row[0]
#                 po_date_str = row[1]
#                 vendor_id = row[2]
#                 quantity = row[3]
#                 unit_price = row[4]
#                 total_price = row[5]
#                 sublocation_name = row[6]
#                 description = row[7]
#                 uom = row[8]
#                 product_id = row[9]

#                 # -----------------------------
#                 # Make timezone-aware datetime
#                 # -----------------------------
#                 dt = datetime.strptime(po_date_str, "%Y-%m-%d %H:%M:%S")
#                 created_at = timezone.make_aware(dt)

#                 # -----------------------------
#                 # Fetch SubLocation & Location
#                 # -----------------------------
#                 try:
#                     subloc_obj = SubLocation.objects.get(name=sublocation_name)
#                     sublocation_id = subloc_obj.id
#                     location_id = subloc_obj.location.id if subloc_obj.location else 1
#                 except SubLocation.DoesNotExist:
#                     print(f"Sublocation '{sublocation_name}' not found, using defaults")
#                     sublocation_id = 1
#                     location_id = 1

#                 # -----------------------------
#                 # HEADER (INSERT ONLY)
#                 # -----------------------------
#                 header_obj, created = PurchaseOrderHeader.objects.get_or_create(
#                     code=po_number,
#                     defaults={
#                         "slug": po_number,
#                         "description": description,
#                         "po_date": created_at.date(),
#                         "requested_delivery_date": created_at.date(),
#                         "po_requested_by_id": 1,
#                         "vendor_id": vendor_id,
#                         "po_status_id": pos.pk,
#                         "qm_header_status_id": pos.pk,
#                         "po_type_id": 1,
#                         "status": 1,
#                         "created_user_id": 1,
#                         "updated_at": created_at,
#                         "created_at": created_at,
#                     }
#                 )

#                 if created:
#                     print(f"Inserted PO Header: {po_number} (ID: {header_obj.id})")
#                 else:
#                     print(f"Skipped existing PO Header: {po_number}")

#                 line_number_cache.setdefault(po_number, 1)
#                 line_number = line_number_cache[po_number]

#                 # -----------------------------
#                 # ITEM (INSERT ONLY)
#                 # -----------------------------
#                 item_code = f"{po_number}-{line_number}"

#                 item_defaults = {
#                     "line_number": line_number,
#                     "quantity": quantity,
#                     "created_at": created_at,
#                     "updated_at": created_at,
#                     "description": description,
#                     "uom": uom,
#                     "unit_price": unit_price,
#                     "total_price": total_price,
#                     "item_status": "OPEN",
#                     "slug": item_code,
#                     "item_id": product_id,
#                     "po_header_id": header_obj.id,
#                     "po_location_id": location_id,
#                     "sub_location_id": sublocation_id,
#                     "qty_inspection_status": "OPEN",
#                     "status": 1,
#                     "already_received_qty": 0,
#                     "qty_being_received": 0,
#                     "yet_to_be_received_qty": 0,
#                     "good_qty": 0,
#                     "rejected_qty": 0,
#                     "total_qty_inspected": 0,
#                     "quality_already_inspected": 0,
#                     "quality_already_rejected": 0,
#                     "created_user_id": 1,
#                 }

#                 item_obj, item_created = PurchaseOrderItem.objects.get_or_create(
#                     code=item_code,
#                     defaults=item_defaults
#                 )

#                 if item_created:
#                     print(f"Inserted PO Item: {item_code}")
#                 else:
#                     print(f"Skipped existing PO Item: {item_code}")

#                 line_number_cache[po_number] += 1

#             self.stdout.write(self.style.SUCCESS("PO Headers & Items inserted successfully"))

#         except Exception as e:
#             self.stderr.write(self.style.ERROR(f"Error: {e}"))

#         finally:
#             source_cursor.close()
#             destination_cursor.close()

from django.core.management.base import BaseCommand
from django.db import connections
from datetime import datetime
from django.utils import timezone
from inventory.models import PurchaseOrderStatus, PurchaseOrderHeader, PurchaseOrderItem
from location.models import SubLocation
from ims.models import Units   # FIX

class Command(BaseCommand):
    help = "Insert PO Header and Items only (no updates)"

    def handle(self, *args, **kwargs):

        source_conn = connections['default']
        source_cursor = source_conn.cursor()

        destination_conn = connections['default']
        destination_cursor = destination_conn.cursor()

        # ------------------------------------------------------------------
        # QUERY SOURCE DATA
        # ------------------------------------------------------------------
        query = """
        SELECT
            po.po_number,
            strftime('%Y-%m-%d %H:%M:%S', po.date_created),
            dpo.sources_id,
            dpo_particular.quantity_dpo,
            dpo_particular.unit_price_dpo,
            dpo_particular.total_value,
            subloc.name,
            p.item_specification,
            unit.unit,
            cp.id
        FROM ims_poapproval AS pa
        JOIN ims_purchase_order AS po ON pa.po_id = po.id
        JOIN ims_dpo AS dpo ON po.draft_po_id = dpo.id
        JOIN ims_procurement AS proce ON dpo.procurement_id = proce.id
        JOIN location_sublocation AS subloc ON proce.branch_id = subloc.id
        JOIN ims_dpo_particular AS dpo_dpos ON dpo.id = dpo_dpos.dpo_id
        JOIN ims_dpoparticular AS dpo_particular ON dpo_dpos.dpoparticular_id = dpo_particular.id
        JOIN ims_quotationparticular AS qp ON dpo_particular.quotation_particular_id = qp.id
        JOIN ims_particular AS p ON qp.csparticular_id = p.id
        JOIN ims_units AS unit ON p.unitname_id = unit.id
        JOIN catalog_product AS cp ON p.product_id = cp.id
        WHERE pa.done_sign = 1
        ORDER BY po.po_number;
        """

        source_cursor.execute(query)
        rows = source_cursor.fetchall()

        print(f"Fetched {len(rows)} rows")

        # ------------------------------------------------------------------
        # CACHES
        # ------------------------------------------------------------------
        line_number_cache = {}

        # Cache units for performance
        units_cache = {u.unit.lower(): u for u in Units.objects.all()}

        # ------------------------------------------------------------------
        # GET STATUS
        # ------------------------------------------------------------------
        pos = PurchaseOrderStatus.objects.get(name='OPEN')

        try:
            for row in rows:

                po_number = row[0]
                po_date_str = row[1]
                vendor_id = row[2]
                quantity = row[3]
                unit_price = row[4]
                total_price = row[5]
                sublocation_name = row[6]
                description = row[7]
                uom_name = row[8]
                product_id = row[9]

                # -----------------------------
                # Make timezone-aware datetime
                # -----------------------------
                dt = datetime.strptime(po_date_str, "%Y-%m-%d %H:%M:%S")
                created_at = timezone.make_aware(dt)

                # -----------------------------
                # Fetch SubLocation & Location
                # -----------------------------
                try:
                    subloc_obj = SubLocation.objects.get(name=sublocation_name)
                    sublocation_id = subloc_obj.id
                    location_id = subloc_obj.location.id if subloc_obj.location else 1

                except SubLocation.DoesNotExist:

                    print(f"Sublocation '{sublocation_name}' not found, using defaults")

                    sublocation_id = 1
                    location_id = 1

                # -----------------------------
                # Convert UOM string → Units instance
                # -----------------------------
                uom_key = (uom_name or "").lower()

                uom_obj = units_cache.get(uom_key)

                if not uom_obj:
                    uom_obj = Units.objects.create(unit=uom_key)
                    units_cache[uom_key] = uom_obj

                # -----------------------------
                # HEADER (INSERT ONLY)
                # -----------------------------
                header_obj, created = PurchaseOrderHeader.objects.get_or_create(

                    code=po_number,

                    defaults={
                        "slug": po_number,
                        "description": description,
                        "po_date": created_at.date(),
                        "requested_delivery_date": created_at.date(),
                        "po_requested_by_id": 1,
                        "vendor_id": vendor_id,
                        "po_status_id": pos.pk,
                        "qm_header_status_id": pos.pk,
                        "po_type_id": 1,
                        "status": 1,
                        "created_user_id": 1,
                        "updated_at": created_at,
                        "created_at": created_at,
                    }
                )

                if created:
                    print(f"Inserted PO Header: {po_number} (ID: {header_obj.id})")
                else:
                    print(f"Skipped existing PO Header: {po_number}")

                line_number_cache.setdefault(po_number, 1)

                line_number = line_number_cache[po_number]

                # -----------------------------
                # ITEM (INSERT ONLY)
                # -----------------------------
                item_code = f"{po_number}-{line_number}"

                item_defaults = {

                    "line_number": line_number,
                    "quantity": quantity,
                    "created_at": created_at,
                    "updated_at": created_at,
                    "description": description,
                    "uom": uom_obj,   # FIXED
                    "unit_price": unit_price,
                    "total_price": total_price,
                    "item_status": "OPEN",
                    "slug": item_code,
                    "item_id": product_id,
                    "po_header_id": header_obj.id,
                    "po_location_id": location_id,
                    "sub_location_id": sublocation_id,
                    "qty_inspection_status": "OPEN",
                    "status": 1,
                    "already_received_qty": 0,
                    "qty_being_received": 0,
                    "yet_to_be_received_qty": 0,
                    "good_qty": 0,
                    "rejected_qty": 0,
                    "total_qty_inspected": 0,
                    "quality_already_inspected": 0,
                    "quality_already_rejected": 0,
                    "created_user_id": 1,
                }

                item_obj, item_created = PurchaseOrderItem.objects.get_or_create(
                    code=item_code,
                    defaults=item_defaults
                )

                if item_created:
                    print(f"Inserted PO Item: {item_code}")
                else:
                    print(f"Skipped existing PO Item: {item_code}")

                line_number_cache[po_number] += 1

            self.stdout.write(self.style.SUCCESS("PO Headers & Items inserted successfully"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error: {e}"))

        finally:
            source_cursor.close()
            destination_cursor.close()