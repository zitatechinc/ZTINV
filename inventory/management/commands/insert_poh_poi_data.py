from django.core.management.base import BaseCommand
from django.db import connections, transaction
from datetime import datetime
from inventory.models import  PurchaseOrderStatus

class Command(BaseCommand):
    help = "Insert PO Header and Items (1 Header → Many Items)"

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
            loc.location,
            p.item_specification,
            unit.unit,
            cp.id
        FROM ims_poapproval AS pa
        JOIN ims_purchase_order AS po ON pa.po_id = po.id
        JOIN ims_dpo AS dpo ON po.draft_po_id = dpo.id
        JOIN ims_procurement AS proce ON dpo.procurement_id = proce.id
        JOIN ims_officebranch AS loc ON proce.branch_id = loc.id
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
        print(rows,"rows")

        # ------------------------------------------------------------------
        # CACHES
        # ------------------------------------------------------------------
        po_header_cache = {}
        line_number_cache = {}

        # ------------------------------------------------------------------
        # SQL STATEMENTS
        # ------------------------------------------------------------------
        pos = PurchaseOrderStatus.objects.get(name='OPEN')
        #print(pos.pk,"1111111111")
        sql_header = """
        INSERT INTO inventory_purchaseorderheader
        (code, slug, created_at, updated_at, description, po_date,
         requested_delivery_date, po_requested_by_id, vendor_id,
         po_status_id, qm_header_status_id, po_type_id, status, created_user_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 1, 1)
        """

        sql_item = """
        INSERT INTO inventory_purchaseorderitem
        (code, line_number, quantity, created_at, updated_at,
         description, uom, unit_price, total_price,
         already_received_qty, qty_being_received, yet_to_be_received_qty,
         item_status, slug, item_id, po_header_id, po_location_id,
         good_qty, rejected_qty, total_qty_inspected,
         quality_already_inspected, quality_already_rejected,
         qty_inspection_status, status, created_user_id)
        VALUES
        (%s, %s, %s, %s, %s, %s, %s, %s, %s,
         0, 0, 0, %s, %s, %s, %s, %s,
         0, 0, 0, 0, 0, %s, 1, 1)
        """

        # ------------------------------------------------------------------
        # PROCESS DATA
        # ------------------------------------------------------------------
        try:
            for row in rows:
                po_number = row[0]
                po_date = row[1]

                dt = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
                date_only = dt.strftime("%Y-%m-%d")

                vendor_id = row[2]
                quantity = row[3]
                unit_price = row[4]
                total_price = row[5]
                location_city = row[6]
                description = row[7]
                uom = row[8]
                product_id = row[9]

                created_at = po_date
                user_id = 1
                item_status = "OPEN"
                qty_inspection_status = "OPEN"
                po_status_id = pos.pk
                qm_header_status_id = pos.pk

                # -----------------------------
                # LOCATION ID
                # -----------------------------
                destination_cursor.execute(
                    "SELECT id FROM location_location WHERE city = %s LIMIT 1",
                    (location_city,)
                )
                loc_row = destination_cursor.fetchone()
                location_id = loc_row[0] if loc_row else 1

                # -----------------------------
                # HEADER (ONCE PER PO)
                # -----------------------------
                if po_number in po_header_cache:
                    po_header_id = po_header_cache[po_number]
                    line_number = line_number_cache[po_number]
                else:
                    destination_cursor.execute(
                        "SELECT id FROM inventory_purchaseorderheader WHERE code = %s",
                        (po_number,)
                    )
                    header_row = destination_cursor.fetchone()

                    if header_row:
                        po_header_id = header_row[0]
                    else:
                        # Insert the header only if it doesn't already exist
                        destination_cursor.execute(sql_header, (
                            po_number, po_number, created_at, created_at,
                            description, date_only, date_only, user_id, vendor_id, po_status_id, qm_header_status_id
                        ))

                        destination_cursor.execute(
                            "SELECT id FROM inventory_purchaseorderheader WHERE code = %s",
                            (po_number,)
                        )
                        po_header_id = destination_cursor.fetchone()[0]

                    po_header_cache[po_number] = po_header_id
                    line_number_cache[po_number] = 1
                    line_number = 1

                # -----------------------------
                # ITEM (ALWAYS)
                # -----------------------------
                item_code = f"{po_number}-{line_number}"

                # Check if the item already exists before inserting
                destination_cursor.execute(
                    "SELECT 1 FROM inventory_purchaseorderitem WHERE code = %s LIMIT 1",
                    (item_code,)
                )
                existing_item = destination_cursor.fetchone()

                if existing_item:
                    # Skip inserting this item if it already exists
                    print(f"Item {item_code} already exists. Skipping insert.")
                    continue

                #item_slug = f"ITEM-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                destination_cursor.execute(sql_item, (
                    item_code,
                    line_number,
                    quantity,
                    created_at,
                    created_at,
                    description,
                    uom,
                    unit_price,
                    total_price,
                    item_status,
                    item_code,
                    product_id,
                    po_header_id,
                    location_id,
                    qty_inspection_status
                ))

                line_number_cache[po_number] += 1

            destination_conn.commit()
            self.stdout.write(self.style.SUCCESS("PO Headers & Items inserted successfully"))

        except Exception as e:
            destination_conn.rollback()
            self.stderr.write(self.style.ERROR(f"Error: {e}"))

        finally:
            source_cursor.close()
            destination_cursor.close()