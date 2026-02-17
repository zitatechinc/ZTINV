from django.views import View
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from .forms import PurchaseOrderTypeModelForm, PurchaseOrderTypeStatusModelForm, PurchaseOrderHeaderModelForm, PurchaseOrderItemModelForm,PONumberForm,GoodsReceiverModelForm,QualityManagementModelForm, GoodsSearchForm,InventorySearchModelForm
from .models import PurchaseOrderType, PurchaseOrderStatus, PurchaseOrderHeader, PurchaseOrderItem
from django.utils import timezone
from django.db import transaction
from application.models import AppSettings
from django.http import HttpResponse
from django.urls import reverse
import re
from core.views import BaseCRUDView, InventoryBaseCRUDView, GoodsReceiverBaseCRUDView, QualityManagementBaseCRUDView, POReportBaseCRUDView, VendorPOBaseCRUDView,InventorySearchBaseCRUDView
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
import traceback
# views.py
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from decimal import Decimal
from django.core.exceptions import ValidationError
from inventory.models import *
from datetime import date
from django.db.models import Sum
from django.template.loader import render_to_string
from rest_framework.response import Response
from rest_framework.decorators import api_view
from xhtml2pdf import pisa # pdf download

@login_required
def create_po(request):
    return render(request, 'inventory/create_po.html', {"page_title" : "Create Purchase Order"})


class PurchaseOrderTypeCRUDView(BaseCRUDView):
    model = PurchaseOrderType
    form_class = PurchaseOrderTypeModelForm
    FieldList = (('name','Name'),
                 ('code','Code'),
                 ('updated_at','Updated at'),
                 ('search_keywords','Search Keywords')
                 )
    def get_extra_context(self):
        
        return {
            
        }

class PurchaseOrderStatusCRUDView(BaseCRUDView):
    model = PurchaseOrderStatus
    form_class = PurchaseOrderTypeStatusModelForm
    FieldList = (('name','Name'),
                 ('code','Code'),
                 ('updated_at','Updated at'),
                 ('search_keywords','Search Keywords')
                 )
    def get_extra_context(self):
        
        return {
            
        }

class PurchaseOrderHeaderCRUDView(InventoryBaseCRUDView):
    model = PurchaseOrderHeader
    form_class = PurchaseOrderHeaderModelForm
    FieldList = (
                 ('code','PO Code'),
                 ('vendor__company_name1','Vendor Company Name1'),
                 ('vendor__code','Vendor Code'),
                 ('updated_at','Updated at'),
                 ('search_keywords','Search Keywords')
                 )
    
    def get_extra_context(self):
        
        return {
            
        }

class PurchaseOrderItemsCRUDView(VendorPOBaseCRUDView):
    model = PurchaseOrderItem
    form_class = PurchaseOrderItemModelForm
    FieldList = (
                 ('code','PO Code'),
                 ('vendor__company_name1','Vendor Company Name1'),
                 ('vendor__code','Vendor Code'),
                 ('updated_at','Updated at'),
                 ('search_keywords','Search Keywords')
                 )
    
    def get_extra_context(self):
        
        return {
            
        }


def goods_receiver(request):
    schedules = None
    po_item_list = None

    if request.method == "POST":
        form = PONumberForm(request.POST)
        if form.is_valid():
            po_number = form.cleaned_data["po_number"].strip()
            po_item_list = settings.PO_ITEM_LIST
    else:
        form = PONumberForm()

    return render(request, "vendor/goods_receiver.html", {
        "form": form,
        #"po_header": po_header,
        "po_item_list": po_item_list,
    })


class GoodsReceiverCrudView(GoodsReceiverBaseCRUDView):
    model = PurchaseOrderHeader
    form_class = GoodsReceiverModelForm
    FieldList = (
                 ('code','PO Code'),
                 ('vendor__company_name1','Vendor Company Name1'),
                 ('vendor__code','Vendor Code'),
                 ('updated_at','Updated at'),
                 ('search_keywords','Search Keywords')
                 )
    
    def get_extra_context(self):
        
        return {
            
        }

class QualityManagementCrudView(QualityManagementBaseCRUDView):
    model = PurchaseOrderHeader
    form_class = QualityManagementModelForm
    FieldList = (
                 ('code','PO Code'),
                 ('vendor__company_name1','Vendor Company Name1'),
                 ('vendor__code','Vendor Code'),
                 ('updated_at','Updated at'),
                 ('search_keywords','Search Keywords')
                 )
    
    def get_extra_context(self):
        
        return {
            
        }

class POReportCrudView(POReportBaseCRUDView):
    model = PurchaseOrderHeader
    form_class = QualityManagementModelForm
    FieldList = (
                 ('code','PO Code'),
                 ('vendor__company_name1','Vendor Company Name1'),
                 ('vendor__code','Vendor Code'),
                 ('updated_at','Updated at'),
                 ('search_keywords','Search Keywords')
                 )
    
    def get_extra_context(self):
        
        return {
            
        }


def process_goods_receipt(
    po_item,
    po_header,
    gm_date,
    gm_quantity,
    quality_already_rejected,
    already_inspected_qty,
    gm_type,
    location=None,
    sub_location=None,
    gm_text="",
    user=None,
):
    """
    Process a Goods Movement for a Purchase Order.
    Steps:
        1. Update PO Item quantities (already received, yet to receive)
        2. Update PO Header status (Open/Partial/Closed)
        3. Upsert Inventory
        4. Insert Goods Movement Item
        5. Insert Purchase Order History

    Args:
        po_item (PurchaseOrderItem): The PO Item being processed
        po_header (PurchaseOrderHeader): The PO Header
        gm_date (date): Goods Movement date
        gm_quantity (Decimal): Quantity being moved
        gm_type (str): "Goods Receipt", "Goods Issue", etc.
        location (Location, optional): Location for inventory
        sub_location (SubLocation, optional): Sub-location
        gm_text (str, optional): Notes for GM Item
        user (User, optional): User performing the operation

    Raises:
        ValidationError: For invalid quantity, negative inventory, or other issues
    """
    
    if gm_quantity < 0:
        raise ValidationError("GM Quantity must be greater than zero.")

    if already_inspected_qty < int(quality_already_rejected):
        raise ValidationError("Rejected Quantity must not be Less than of Inspection qty.")

    try:
        with transaction.atomic():
            # -----------------------------
            # 1. Update PO Item
            # -----------------------------
            #print("po_item.already_received_qty ===>>>",po_item.already_received_qty)
            #print("gm_quantity ===>>>",gm_quantity)

            po_item.already_received_qty += Decimal(gm_quantity) if gm_type in ["Goods Receipt", "Receipt","Quality Management"] else Decimal('0.00')
            #print("po_item.quantity ===>>>",po_item.quantity)
            #print("po_item.already_received_qty ===>>>",po_item.already_received_qty)
            po_item.yet_to_be_received_qty = max(po_item.quantity - po_item.already_received_qty, 0)
            #print("po_item.yet_to_be_received_qty --->>>",po_item.yet_to_be_received_qty)

            # print(quality_already_rejected,"quality_already_rejected======")
            # print(ins_qty,"ins_qty=========")
            good_qty_items = already_inspected_qty - quality_already_rejected
            po_item.good_qty += already_inspected_qty - quality_already_rejected
            po_item.rejected_qty += quality_already_rejected

            aldy_rec_qty = int(po_item.already_received_qty)
            ins_qty = po_item.good_qty + po_item.rejected_qty
            po_item.total_qty_inspected =  aldy_rec_qty - ins_qty

            # if int(po_item.total_qty_inspected) < (int(quality_already_rejected) + int(already_inspected_qty)):
            #     raise ValidationError(
            #         "Rejected Quantity & Inspected Qty must not be greater than Received Quantity."
            #     )
          
            # -----------------------------
            # 2. Update PO Header status
            # -----------------------------
            if po_item.yet_to_be_received_qty == 0:
                po_item.item_status = PurchaseOrderStatus.objects.get(name="CLOSED").name
            elif po_item.already_received_qty > 0:
                po_item.item_status = PurchaseOrderStatus.objects.get(name="PARTIAL").name
            else:
                po_item.item_status = PurchaseOrderStatus.objects.get(name="OPEN").name
           
            
            # -----------------------------------
            # 3. Update POI qty_inspection_status
            # ------------------------------------
            if po_item.quantity == po_item.good_qty + po_item.rejected_qty:
                po_item.qty_inspection_status = PurchaseOrderStatus.objects.get(name="CLOSED").name
            elif po_item.good_qty > 0:
                po_item.qty_inspection_status = PurchaseOrderStatus.objects.get(name="PARTIAL").name
            else:
                po_item.qty_inspection_status = PurchaseOrderStatus.objects.get(name="OPEN").name
                
            
            po_item.save()
            
            # -----------------------------
            # 4. Inventory Upsert
            # -----------------------------
            
            if gm_type == "Quality Management":
                inventory, _ = Inventory.objects.get_or_create(
                    product=po_item.item,
                    location=location,
                    sub_location=sub_location,
                    inventory_type="FG",
                    defaults={'quantity': Decimal('0.00')}
                )

                if gm_type == "Quality Management":
                    inventory.quantity += Decimal(good_qty_items)
                elif gm_type in ["Goods Issue"]:
                    inventory.quantity -= Decimal(good_qty_items)

                if inventory.quantity < 0:
                    raise ValidationError("Inventory cannot be negative.")

                # if gm_type in ["Goods Receipt", "Receipt", "Quality Management"]:
                #     inventory.quantity += Decimal(gm_quantity)
                # elif gm_type in ["Goods Issue"]:
                #     inventory.quantity -= Decimal(gm_quantity)

                # if inventory.quantity < 0:
                #     raise ValidationError("Inventory cannot be negative.")

                inventory.save()

            # -----------------------------
            # 5. Insert Goods Movement Item
            # -----------------------------
            print(f"GM-{po_header.code}-{po_item.line_number}")

        
            document_number =GoodsMovementHeader.objects.filter(
                po_header=po_header,
                po_item=po_item                   
            )
            
            if gm_type in ("Goods Receipt", "Receipt"):
                prefix = "GM"
            elif gm_type == "Quality Management":
                prefix = "QM"
            else:
                prefix = "GM"

            if prefix:
                increment_number = len(document_number) + 1 if len(document_number) > 0 else 1
                gm_code = f"{prefix}-{po_header.code}-{po_item.line_number}_{increment_number}"


            print("document_number:",gm_code)
            gm_item = GoodsMovementItem.objects.create(
                document_number=GoodsMovementHeader.objects.create(
                    code=gm_code,
                    category=gm_type,
                    gm_date=gm_date,
                    gm_posting_date=gm_date,
                    po_header=po_header,
                    po_item=po_item,
                    description=gm_text
                ),
                code=gm_code,
                item_number=po_item.line_number,
                product=po_item.item,
                location=location,
                sub_location=sub_location,
                quantity=Decimal(good_qty_items),
                uom=po_item.uom,
                gm_type=gm_type,
                gm_item_text=gm_text
            )

            # -----------------------------
            # 6. Insert PO History
            # -----------------------------
            if gm_type == "Goods Receipt":
                po_history_type = "GR"
            elif gm_type == "Quality Management":
                po_history_type = "QM"
            else:
                po_history_type = "WA"
            PurchaseOrderHistory.objects.create(
                po_header=po_header,
                po_line_number=po_item.line_number,
                product=po_item,
                po_history_number=gm_item.item_number,
                po_history_type=po_history_type,
                description=gm_text,
                gm_header=gm_item.document_number,
                po_history_date=gm_date,
                po_quantity=Decimal(gm_quantity),
                po_line_amount=Decimal(gm_quantity) * po_item.unit_price,
                uom=po_item.uom,
                po_good_qty = already_inspected_qty - quality_already_rejected,
                po_rejected_qty = quality_already_rejected
            )

            # -----------------------------
            # 7. Generate Serial Numbers
            # -----------------------------

            product = po_item.item
            if getattr(product, "serialnumber_status", 0) == 1:
                prefix = product.prefix 
                existing_count = SerialNumber.objects.filter(product=product).count()

                serial_list = []
                for i in range(1, int(gm_quantity) + 1):
                    serial_no = f"{prefix}-{existing_count + i:05d}"  # e.g., ABC-00001
                    sn = SerialNumber.objects.create(
                        product=product,
                        po_item=po_item,
                        gm_header_id = gm_item.document_number.pk,
                        gm_item=gm_item,
                        po_header=po_header,
                        serial_number=serial_no,
                        location=location,
                        sub_location=sub_location,
                        
                    )
                    serial_list.append(serial_no)
                print(f"Generated Serials for {product.name}: {serial_list}")


            return gm_item  # return created GM Item

    except ValidationError as ve:
        # Rollback transaction on known validation issues
        raise ve
    except Exception as e:
        # Rollback transaction on unexpected issues
        raise ValidationError(f"Error processing PO Goods Movement: {str(e)}")

def bulk_goods_receipt(request, po_id):
    po_obj = get_object_or_404(PurchaseOrderHeader, id=po_id)

    if request.method == "POST":
        item_errors = {}
        processed = 0
        ht_items_list = []
        for item in po_obj.items.all():
            field_name = f"qty_being_received_{item.id}"
            qty_str = request.POST.get(field_name, "0")

            already_rejected_field_name = f"quality_already_rejected_{item.id}"
            already_rejected_qty_str = request.POST.get(already_rejected_field_name, "0")

            already_inspected_field_name = f"quality_already_inspected_{item.id}"
            already_inspected_qty_str = request.POST.get(already_inspected_field_name, "0")

            try:
                qty_being_received = float(qty_str)
            except ValueError:
                qty_being_received = 0

            try:
                quality_already_rejected = float(already_rejected_qty_str)
            except ValueError:
                quality_already_rejected = 0

            try:
                already_inspected_qty = float(already_inspected_qty_str)
            except ValueError:
                already_inspected_qty = 0    

            # Collect row-specific errors
            row_errors = []

            if qty_being_received < 0:
                row_errors.append("Quantity cannot be negative.")

            if qty_being_received > float(item.yet_to_be_received):
                row_errors.append(
                    f"Quantity ({qty_being_received}) exceeds yet to be received ({item.yet_to_be_received})."
                )

            if float(item.already_received_qty) + float(qty_being_received) > float(item.quantity):
                row_errors.append(
                    f"Total received ({float(item.already_received_qty) + float(qty_being_received)}) "
                    f"cannot exceed ordered quantity ({item.quantity})."
                )

            if row_errors:
                item_errors[item.id] = row_errors
                continue    
            
            # Process valid rows
            if qty_being_received > 0 or quality_already_rejected > 0 or already_inspected_qty > 0:
                gm_date_str = date.today().strftime("%Y-%m-%d")
                process_goods_receipt(
                    po_header=po_obj,
                    po_item=item,
                    gm_date=gm_date_str,
                    gm_type="Goods Receipt",
                    gm_quantity=qty_being_received,
                    quality_already_rejected= quality_already_rejected,
                    already_inspected_qty=already_inspected_qty,
                    location=item.po_location,
                    sub_location=item.sub_location,
                    user=request.user,
                )
                processed += 1
                ht_items_list.append(item.pk)
         # -----------------------------------
        #  Update PO Header Status
        # -----------------------------------
        all_items = po_obj.items.all()
        statuses = [item.item_status for item in all_items]

        if all(s == "CLOSED" for s in statuses):
            po_obj.po_status = PurchaseOrderStatus.objects.get(name="CLOSED")
        elif all(s == "OPEN" for s in statuses):
            po_obj.po_status = PurchaseOrderStatus.objects.get(name="OPEN")
        else:
            po_obj.po_status = PurchaseOrderStatus.objects.get(name="PARTIAL")

        po_obj.save()
        # Save errors into session for re-render
        request.session["item_errors"] = item_errors
        request.session["last_po_id"] = po_id
        request.session['ht_items_list']=ht_items_list

        # Summary message
        if processed and not item_errors:
            messages.success(request, f"✅ {processed} items processed successfully.")
        elif processed and item_errors:
            messages.warning(request, f"⚠️ {processed} items processed, but some errors exist.")
        elif not processed and not item_errors:
            messages.info(request, "ℹ️ No quantities entered.")

    return redirect(f"{reverse('goods-receiver-create')}?po_id={po_id}")


def quality_management_receipt(request, po_id):
    po_obj = get_object_or_404(PurchaseOrderHeader, id=po_id)

    if request.method == "POST":
        item_errors = {}
        processed = 0
        ht_items_list = []
        for item in po_obj.items.all():
            field_name = f"qty_being_received_{item.id}"
            data = request.POST
            print("data",data)

            qty_str = request.POST.get(field_name, "0")

            already_rejected_field_name = f"quality_already_rejected_{item.id}"
            already_rejected_qty_str = request.POST.get(already_rejected_field_name, "0")

            already_inspected_field_name = f"quality_already_inspected_{item.id}"
            already_inspected_qty_str = request.POST.get(already_inspected_field_name, "0")
            qm_notes = request.POST.get(f'qm_notes_{item.pk}','')

            try:
                qty_being_received = float(qty_str)
            except ValueError:
                qty_being_received = 0

            try:
                quality_already_rejected = float(already_rejected_qty_str)
            except ValueError:
                quality_already_rejected = 0

            try:
                already_inspected_qty = float(already_inspected_qty_str)
            except ValueError:
                already_inspected_qty = 0    

            # Collect row-specific errors
            row_errors = []

            if qty_being_received < 0:
                row_errors.append("Quantity cannot be negative.")

            if qty_being_received > float(item.yet_to_be_received):
                row_errors.append(
                    f"Quantity ({qty_being_received}) exceeds yet to be received ({item.yet_to_be_received})."
                )

            if float(item.already_received_qty) + float(qty_being_received) > float(item.quantity):
                row_errors.append(
                    f"Total received ({float(item.already_received_qty) + float(qty_being_received)}) "
                    f"cannot exceed ordered quantity ({item.quantity})."
                )

            if row_errors:
                item_errors[item.id] = row_errors
                continue    
            item.qm_notes= qm_notes
            # Process valid rows
            if qty_being_received > 0 or quality_already_rejected > 0 or already_inspected_qty > 0:
                gm_date_str = date.today().strftime("%Y-%m-%d")
                process_goods_receipt(
                    po_header=po_obj,
                    po_item=item,
                    gm_date=gm_date_str,
                    gm_type="Quality Management",
                    gm_quantity=qty_being_received,
                    quality_already_rejected= quality_already_rejected,
                    already_inspected_qty=already_inspected_qty,
                    location=item.po_location,
                    sub_location=item.sub_location,
                    user=request.user,
                )
                processed += 1
                ht_items_list.append(item.pk)
         # -----------------------------------
        #  Update PO Header Status
        # -----------------------------------
        all_items = po_obj.items.all()
        statuses = [item.qty_inspection_status for item in all_items]

        if all(s == "CLOSED" for s in statuses):
            po_obj.qm_header_status = PurchaseOrderStatus.objects.get(name="CLOSED")
        elif all(s == "OPEN" for s in statuses):
            po_obj.qm_header_status = PurchaseOrderStatus.objects.get(name="OPEN")
        else:
            po_obj.qm_header_status = PurchaseOrderStatus.objects.get(name="PARTIAL")

        po_obj.save()
        # Save errors into session for re-render
        request.session["item_errors"] = item_errors
        request.session["last_po_id"] = po_id
        request.session['ht_items_list']=ht_items_list

        # Summary message
        if processed and not item_errors:
            messages.success(request, f"✅ {processed} items processed successfully.")
        elif processed and item_errors:
            messages.warning(request, f"⚠️ {processed} items processed, but some errors exist.")
        elif not processed and not item_errors:
            messages.info(request, "ℹ️ No quantities entered.")

    return redirect(f"{reverse('quality-management-create')}?po_id={po_id}")


class InventorySearchCrudView(InventorySearchBaseCRUDView):
    model = Inventory
    form_class = InventorySearchModelForm
    
    def get_extra_context(self):
        
        return {
            
        }


def inventory_gm_history(request):
    """Return an HTML fragment listing GoodsMovementItem rows filtered by product/location/sub_location."""
    product_id = request.GET.get('product_id')
    location_id = request.GET.get('location_id')
    sub_location_id = request.GET.get('sub_location_id')
    # Build base queryset (not sliced) to compute aggregates
    base_qs = GoodsMovementItem.objects.select_related('product', 'location', 'sub_location')
    if product_id:
        base_qs = base_qs.filter(product_id=product_id)
    if location_id:
        base_qs = base_qs.filter(location_id=location_id)
    if sub_location_id:
        base_qs = base_qs.filter(sub_location_id=sub_location_id)

    # Total quantity across matching GM items (without slicing)
    total_qty = base_qs.aggregate(total=Sum('quantity'))['total'] or 0

    # Optional sorting: allow client to request a sort field and direction (safe whitelist)
    sort_field = request.GET.get('sort', 'created_at')
    sort_dir = request.GET.get('dir', 'desc')
    gm_allowed = ('created_at', 'quantity', 'gm_type')
    if sort_field not in gm_allowed:
        sort_field = 'created_at'
    ordering = ('-' + sort_field) if sort_dir == 'desc' else sort_field

    # Limit rows for display (apply ordering after filters)
    qs = base_qs.order_by(ordering)

    # Attempt to resolve the product/location/sub_location objects for header display
    product_obj = None
    location_obj = None
    sub_location_obj = None
    try:
        if product_id:
            product_obj = Product.objects.filter(id=product_id).first()
        elif qs:
            # if not provided, take from first returned row
            first = qs[0]
            product_obj = first.product

        if location_id:
            location_obj = Location.objects.filter(id=location_id).first()
        elif qs:
            first = qs[0]
            location_obj = first.location

        if sub_location_id:
            sub_location_obj = SubLocation.objects.filter(id=sub_location_id).first()
        elif qs:
            first = qs[0]
            sub_location_obj = first.sub_location
    except Exception:
        # defensive: leave objects as None on any lookup error
        product_obj = product_obj or None
        location_obj = location_obj or None
        sub_location_obj = sub_location_obj or None

    html = render_to_string('vendor/gm_history_table.html', {
        'gm_items': qs,
        'product': product_obj,
        'location': location_obj,
        'sub_location': sub_location_obj,
        'total_qty': total_qty,
    })
    return HttpResponse(html)


def inventory_serial_numbers(request):
    """Return an HTML fragment listing SerialNumber rows filtered by product/location/sub_location."""
    product_id = request.GET.get('product_id')
    location_id = request.GET.get('location_id')
    sub_location_id = request.GET.get('sub_location_id')

    base_qs = SerialNumber.objects.select_related('product', 'location', 'sub_location', 'po_header', 'gm_header')
    if product_id:
        base_qs = base_qs.filter(product_id=product_id)
    if location_id:
        base_qs = base_qs.filter(location_id=location_id)
    if sub_location_id:
        base_qs = base_qs.filter(sub_location_id=sub_location_id)

    total_count = base_qs.count()
    # Optional sorting: allow client to request a sort field and direction (safe whitelist)
    sort_field = request.GET.get('sort', 'serial_number')
    sort_dir = request.GET.get('dir', 'asc')
    serial_allowed = ('serial_number', 'created_at')
    if sort_field not in serial_allowed:
        sort_field = 'serial_number'
    ordering = ('-' + sort_field) if sort_dir == 'desc' else sort_field

    # Apply ordering after filtering
    qs = base_qs.order_by(ordering)[:500]

    product_obj = None
    location_obj = None
    sub_location_obj = None
    try:
        if product_id:
            product_obj = Product.objects.filter(id=product_id).first()
        elif qs:
            product_obj = qs[0].product

        if location_id:
            location_obj = Location.objects.filter(id=location_id).first()
        elif qs:
            location_obj = qs[0].location

        if sub_location_id:
            sub_location_obj = SubLocation.objects.filter(id=sub_location_id).first()
        elif qs:
            sub_location_obj = qs[0].sub_location
    except Exception:
        product_obj = product_obj or None
        location_obj = location_obj or None
        sub_location_obj = sub_location_obj or None

    html = render_to_string('vendor/serial_number_table.html', {
        'serials': qs,
        'product': product_obj,
        'location': location_obj,
        'sub_location': sub_location_obj,
        'total_count': total_count,
    })
    return HttpResponse(html)    


@api_view(['GET'])
def PO_list(request):
    po_objs = PurchaseOrderHeader.objects.all().order_by('-created_at')
    data = []
    for po_obj in po_objs:
        data.append({
            "id": po_obj.id,
            "code": po_obj.code,
            "create_at":po_obj.updated_at,
            "vendor_code": po_obj.vendor.code,
            "vendor_name" : po_obj.vendor.company_name1
        })
    return Response({"data": data})


def inspection_receipt_view(request):
    print("INSIDE INSPECTION RECEIPT VIEW")  # This should show up in the terminal if the view is being hit
    context = {
        "supplier": "M/s Riddhi Enterprises",
        "indentor": "Nagesh",
        "document_no": "1026626",
        "document_date": "02.09.25",
        "document_number": "20217726",
        "purchase_order_ref": "166/2025-26",
        "invoice_dc": "DD",
        "rr_lr_dd_hand": "DD",
        "gr": "672",
        "document_date1": "05.08.25",
        "document_date2": "25.08.25",
        "document_date3": "25.08.25",
        "document_date4": "25.08.25",
        "receiving_stores": [
            {
                "material_code": "HF290",
                "description": "Cable Assy with SMA Male",
                "part_no": "95-901-171-12.0M",
                "unit": "No's",
                "ordered_qty": 40,
                "challan_qty": 40,
                "received_qty": 40,
            }
        ],
        "inspection_department": [
            {
                "material_code": "HF290",
                "unit": "No's",
                "received_qty": 40,
                "accepted_qty": 30,
                "rejected_qty": 10,
                "rejected_code": "ABC",
                "accepted_value": "Emplty",
            }
        ],
        "rejected_doc_no_date": "",
        "inspection_signature": "G. Sabry",
        "inspection_sign_date": "08/08/2025",
        "inspection_name_designation": "G. Sabry / QA",
        "stores_signature": "B. Mukul",
        "stores_sign_date": "26/01/25",
        "stores_name_designation": "B. Mukul",
    }
    return render(request, 'inventory/inspection_receipt.html', context)


def quality_management_pdf(request,pk=None):
    
    po_obj = get_object_or_404(PurchaseOrderHeader, pk=pk)
    context ={"po_obj":po_obj}
    #grouped_items = build_grouped_items(po_obj)

   
    html = render_to_string('inventory/inspection_receipt.html', context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="inspection_receipt.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse(f'We had some errors <pre>{html}</pre>')
    return response


# views.py
# from django.shortcuts import render
# from django.http import JsonResponse
# from django.views.decorators.http import require_GET
# from django.utils.dateparse import parse_date
# from .models import PurchaseOrderItem



# def po_item_report_page(request):
#     """
#     Returns the HTML page
#     """
#     return render(request, "templates/inventory/po_item_report.html")


# # 🔹 2. API VIEW
# @require_GET
# def purchase_order_item_report_api(request):
#     """
#     Returns JSON data based on start_date and end_date
#     """
#     start_date = request.GET.get("start_date")
#     end_date = request.GET.get("end_date")

#     if not start_date or not end_date:
#         return JsonResponse(
#             {"error": "start_date and end_date are required"},
#             status=400
#         )

#     start_date = parse_date(start_date)
#     end_date = parse_date(end_date)

#     if not start_date or not end_date:
#         return JsonResponse(
#             {"error": "Invalid date format. Use YYYY-MM-DD"},
#             status=400
#         )

#     items = PurchaseOrderItem.objects.filter(
#         created_at__date__range=(start_date, end_date)
#     ).select_related(
#         "po_header", "item"
#     ).order_by("-created_at")

#     results = []
#     for item in items:
#         results.append({
#             "id": item.id,
#             "code": item.code,
#             "line_number": item.line_number,
#             "product": str(item.item),
#             "quantity": float(item.quantity),
#             "uom": item.uom,
#             "unit_price": float(item.unit_price),
#             "total_price": float(item.total_price or 0),
#             "item_status": item.item_status,
#             "created_at": item.created_at.strftime("%Y-%m-%d %H:%M"),
#         })

#     return JsonResponse({
#         "count": len(results),
#         "results": results
#     })

