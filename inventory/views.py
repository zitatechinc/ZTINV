from django.views import View
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from .forms import PurchaseOrderTypeModelForm, PurchaseOrderTypeStatusModelForm, PurchaseOrderHeaderModelForm, PurchaseOrderItemModelForm,PONumberForm,GoodsReceiverModelForm,QualityManagementModelForm, GoodsSearchForm,InventorySearchModelForm
from .models import PurchaseOrderType, PurchaseOrderStatus, PurchaseOrderHeader, PurchaseOrderItem,PurchaseOrderHistoryRejection,PurchaseOrderHistoryDocument
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

from ims.models import Purchase_Order, Procurement,ProcurementType, SourceOfMake
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
import os

from rest_framework import status
import logging
logger = logging.getLogger(__name__)
logger = logging.getLogger('console')

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


from django.db.models.functions import Substr, Cast
from django.db.models import Max, IntegerField

def generate_prv_number(po_header, gmh_obj, prefix):
    try:
        # Get Purchase Order Header
        po_obj = get_object_or_404(PurchaseOrderHeader, pk=po_header.id)
                    
        #po_obj_pk = PurchaseOrderHeader.objects.get(pk=pk)
        po = Purchase_Order.objects.get(po_number=po_obj.code)

        proc_obj = Procurement.objects.get(id=po.procurement_id)
    except ObjectDoesNotExist as e:
        raise ValueError(f"Required record not found: {e}")

    #Determine Category Number
    category_number = None
    if proc_obj.pr_events == 'Online_order':
        category_number = 5
    elif proc_obj.category_events == 'Sub_Contract':
        category_number = 3
    elif proc_obj.category_events == 'Service_Contract':
        category_number = 6
    elif proc_obj.category_events == 'Meslova_Material':
        category_number = 7
    else:
        try:
            proc_type_obj = ProcurementType.objects.get(id=proc_obj.procurement_type_id)
            source_type_obj = SourceOfMake.objects.get(id=proc_obj.import_indigenous_id)
        except ObjectDoesNotExist as e:
            raise ValueError(f"Related record missing: {e}")
        if proc_type_obj.Procurement_name == 'Capital':
            category_number = 4
        elif proc_type_obj.Procurement_name == 'Revenue':
            if source_type_obj.source_type == 'Imported':
                category_number = 1
            elif source_type_obj.source_type == 'Indigenous':
                category_number = 2
    
    # Final safety check
    if category_number is None:
        raise ValueError("Unable to determine category number.")

    #get the current year’s last two digits
    year_last_two = datetime.now().strftime("%y")
    #generate 4 digit number
    gmh_id = f"{gmh_obj.pk:04d}"

    if prefix == 'GM':
        reference_number = f"PRV{category_number}{gmh_id}{year_last_two}"
    elif prefix =='QM':
        latest_seq = (
            PurchaseOrderHistory.objects
            .filter(reference_number__startswith='IRV')
            .annotate(seq=Cast(Substr('reference_number', 5, 4), IntegerField()))
            .order_by('-updated_at')
            .values_list('seq', flat=True)
            .first()
        )
        next_seq = (latest_seq or 0) + 1
        formatted_seq = f"{next_seq:04d}" if next_seq else ""
        print(latest_seq, formatted_seq)

        reference_number = f"IRV{category_number}{formatted_seq}{year_last_two}"
    return reference_number


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
    reference_number=None,
    document_number=None,
    gr_number= None,
    gr_file=None,
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

        
            # document_number =GoodsMovementHeader.objects.filter(
            #     po_header=po_header,
            #     po_item=po_item                   
            # )

            gmi_list = GoodsMovementItem.objects.all()
            
            if gm_type in ("Goods Receipt", "Receipt"):
                prefix = "GM"
            elif gm_type == "Quality Management":
                prefix = "QM"
            else:
                prefix = "GM"

            if prefix:
                increment_number = len(gmi_list) + 1 if len(gmi_list) > 0 else 1
                gm_code = f"{prefix}-{po_header.code}-{po_item.line_number}_{increment_number}"
    
            gm_item = GoodsMovementItem.objects.create(
                document_number=document_number,
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

            # is_exists = PurchaseOrderHistory.objects.filter(gr_number__iexact=gr_number).exists()
            # if is_exists:
            #     raise ValidationError("GR Number already exists");
            
            po_history =PurchaseOrderHistory.objects.create(
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
                po_rejected_qty = quality_already_rejected,
                reference_number=reference_number,
                gr_number= gr_number,
                gr_file=gr_file,
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


            return po_history  # return created GM Item

    except ValidationError as ve:
        # Rollback transaction on known validation issues
        #raise ve
        raise ValidationError(f"ve: {', '.join(ve.messages)}")
    except Exception as e:
        # Rollback transaction on unexpected issues
        raise ValidationError(f"Error processing PO Goods Movement: {str(e)}")

def bulk_goods_receipt(request, po_id):
    po_obj = get_object_or_404(PurchaseOrderHeader, id=po_id)
    if request.method == "POST":
        item_errors = {}
        processed = 0
        ht_items_list = []

        #new
        document_number =GoodsMovementHeader.objects.filter(
            po_header=po_obj                  
        )
        prefix = "GM"
        gm_date_str = date.today().strftime("%Y-%m-%d")

        if prefix:
            increment_number = len(document_number) + 1 if len(document_number) > 0 else 1
            gm_code = f"{prefix}-{po_obj.code}-{increment_number}"

        gm_obj = GoodsMovementHeader.objects.create(
                code=gm_code,
                category='Goods Receipt',
                gm_date=gm_date_str,
                gm_posting_date=gm_date_str,
                po_header=po_obj
            )

        reference_number = generate_prv_number(po_obj, gm_obj, prefix)
        
        gr_number = request.POST.get('gr_number', "")
        gr_file = request.FILES.get('gr_file')
        
        try:
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
                    # gm_date_str = date.today().strftime("%Y-%m-%d")
                    process_goods_receipt(
                        
                        po_item=item,
                        po_header=po_obj,
                        gm_date=gm_date_str,
                        gm_type="Goods Receipt",
                        gm_quantity=qty_being_received,
                        quality_already_rejected= quality_already_rejected,
                        already_inspected_qty=already_inspected_qty,
                        location=item.po_location,
                        sub_location=item.sub_location,
                        user=request.user,
                        reference_number=reference_number,
                        document_number=gm_obj,
                        gr_number= gr_number,
                        gr_file=gr_file,
                    )
                    processed += 1
                    ht_items_list.append(item.pk)
        except Exception as e:
            print(e)
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

# from django.db import transaction

# @transaction.atomic
# def process_goods_receipt(
#     po_item,
#     po_header,
#     gm_date,
#     gm_quantity,
#     quality_already_rejected,
#     already_inspected_qty,
#     gm_type,
#     location=None,
#     sub_location=None,
#     gm_text="",
#     user=None,
# ):

#     gm_quantity = Decimal(gm_quantity)
#     rejected_qty = Decimal(quality_already_rejected)
#     inspected_qty = Decimal(already_inspected_qty)

#     if rejected_qty > inspected_qty:
#         raise ValidationError("Rejected qty cannot exceed inspected qty.")

#     good_qty = inspected_qty - rejected_qty

#     # ----------------------------
#     # Update PO Item
#     # ----------------------------
#     po_item.already_received_qty += gm_quantity
#     po_item.yet_to_be_received_qty = po_item.quantity - po_item.already_received_qty

#     po_item.good_qty += good_qty
#     po_item.rejected_qty += rejected_qty
#     aldy_rec_qty = int(po_item.already_received_qty)
#     ins_qty = po_item.good_qty + po_item.rejected_qty
#     po_item.total_qty_inspected =  aldy_rec_qty - ins_qty

#     if int(po_item.total_qty_inspected) < (int(quality_already_rejected) + int(already_inspected_qty)):
#         raise ValidationError(
#             "Rejected Quantity & Inspected Qty must not be greater than Received Quantity."
#         )

#     # Item status
#     if po_item.yet_to_be_received_qty <= 0:
#         po_item.item_status = "CLOSED"
#     elif po_item.already_received_qty > 0:
#         po_item.item_status = "PARTIAL"
#     else:
#         po_item.item_status = "OPEN"

#     # Inspection status
#     if po_item.good_qty + po_item.rejected_qty >= po_item.quantity:
#         po_item.qty_inspection_status = "CLOSED"
#     elif po_item.good_qty > 0 or po_item.rejected_qty > 0:
#         po_item.qty_inspection_status = "PARTIAL"
#     else:
#         po_item.qty_inspection_status = "OPEN"

#     po_item.save()

#     # ----------------------------
#     # Inventory Update (Good Qty Only)
#     # ----------------------------
#     inventory, _ = Inventory.objects.get_or_create(
#         product=po_item.item,
#         location=location,
#         sub_location=sub_location,
#         inventory_type="FG",
#         defaults={"quantity": Decimal("0.00")},
#     )

#     inventory.quantity += good_qty

#     if inventory.quantity < 0:
#         raise ValidationError("Inventory cannot be negative.")

#     inventory.save()

#     # ----------------------------
#     # Create Goods Movement
#     # ----------------------------
#     count = GoodsMovementHeader.objects.filter(
#         po_header=po_header,
#         po_item=po_item
#     ).count() + 1

#     gm_code = f"QM-{po_header.code}-{po_item.line_number}-{count}"

#     gm_header = GoodsMovementHeader.objects.create(
#         code=gm_code,
#         category=gm_type,
#         gm_date=gm_date,
#         gm_posting_date=gm_date,
#         po_header=po_header,
#         po_item=po_item,
#         description=gm_text,
#     )

#     GoodsMovementItem.objects.create(
#         document_number=gm_header,
#         code=gm_code,
#         item_number=po_item.line_number,
#         product=po_item.item,
#         location=location,
#         sub_location=sub_location,
#         quantity=good_qty,
#         uom=po_item.uom,
#         gm_type=gm_type,
#         gm_item_text=gm_text,
#     )

#     # ----------------------------
#     # Create PO History
#     # ----------------------------
#     po_history = PurchaseOrderHistory.objects.create(
#         po_header=po_header,
#         po_line_number=po_item.line_number,
#         product=po_item,
#         po_history_number=po_item.history.count() + 1,
#         po_history_type="QM",
#         description=gm_text,
#         gm_header=gm_header,
#         po_history_date=gm_date,
#         po_quantity=gm_quantity,
#         po_line_amount=gm_quantity * po_item.unit_price,
#         uom=po_item.uom,
#         po_good_qty=good_qty,
#         po_rejected_qty=rejected_qty,
#     )

#     return po_history

# def quality_management_receipt(request, po_id):
#     po_obj = get_object_or_404(PurchaseOrderHeader, id=po_id)

#     if request.method == "POST":
#         item_errors = {}
#         processed = 0
#         ht_items_list = []
#         for item in po_obj.items.all():
#             field_name = f"qty_being_received_{item.id}"
#             data = request.POST
#             print("data",data)

#             qty_str = request.POST.get(field_name, "0")

#             already_rejected_field_name = f"quality_already_rejected_{item.id}"
#             already_rejected_qty_str = request.POST.get(already_rejected_field_name, "0")

#             already_inspected_field_name = f"quality_already_inspected_{item.id}"
#             already_inspected_qty_str = request.POST.get(already_inspected_field_name, "0")
#             qm_notes = request.POST.get(f'qm_notes_{item.pk}','')

#             try:
#                 qty_being_received = float(qty_str)
#             except ValueError:
#                 qty_being_received = 0

#             try:
#                 quality_already_rejected = float(already_rejected_qty_str)
#             except ValueError:
#                 quality_already_rejected = 0

#             try:
#                 already_inspected_qty = float(already_inspected_qty_str)
#             except ValueError:
#                 already_inspected_qty = 0    

#             # Collect row-specific errors
#             row_errors = []

#             if qty_being_received < 0:
#                 row_errors.append("Quantity cannot be negative.")

#             if qty_being_received > float(item.yet_to_be_received):
#                 row_errors.append(
#                     f"Quantity ({qty_being_received}) exceeds yet to be received ({item.yet_to_be_received})."
#                 )

#             if float(item.already_received_qty) + float(qty_being_received) > float(item.quantity):
#                 row_errors.append(
#                     f"Total received ({float(item.already_received_qty) + float(qty_being_received)}) "
#                     f"cannot exceed ordered quantity ({item.quantity})."
#                 )

#             if row_errors:
#                 item_errors[item.id] = row_errors
#                 continue    
#             item.qm_notes= qm_notes
#             # Process valid rows
#             if qty_being_received > 0 or quality_already_rejected > 0 or already_inspected_qty > 0:
#                 gm_date_str = date.today().strftime("%Y-%m-%d")
#                 process_goods_receipt(
#                     po_header=po_obj,
#                     po_item=item,
#                     gm_date=gm_date_str,
#                     gm_type="Quality Management",
#                     gm_quantity=qty_being_received,
#                     quality_already_rejected= quality_already_rejected,
#                     already_inspected_qty=already_inspected_qty,
#                     location=item.po_location,
#                     sub_location=item.sub_location,
#                     user=request.user,
#                 )
#                 processed += 1
#                 ht_items_list.append(item.pk)
#          # -----------------------------------
#         #  Update PO Header Status
#         # -----------------------------------
#         all_items = po_obj.items.all()
#         statuses = [item.qty_inspection_status for item in all_items]

#         if all(s == "CLOSED" for s in statuses):
#             po_obj.qm_header_status = PurchaseOrderStatus.objects.get(name="CLOSED")
#         elif all(s == "OPEN" for s in statuses):
#             po_obj.qm_header_status = PurchaseOrderStatus.objects.get(name="OPEN")
#         else:
#             po_obj.qm_header_status = PurchaseOrderStatus.objects.get(name="PARTIAL")

#         po_obj.save()
#         # Save errors into session for re-render
#         request.session["item_errors"] = item_errors
#         request.session["last_po_id"] = po_id
#         request.session['ht_items_list']=ht_items_list

#         # Summary message
#         if processed and not item_errors:
#             messages.success(request, f"✅ {processed} items processed successfully.")
#         elif processed and item_errors:
#             messages.warning(request, f"⚠️ {processed} items processed, but some errors exist.")
#         elif not processed and not item_errors:
#             messages.info(request, "ℹ️ No quantities entered.")

#     return redirect(f"{reverse('quality-management-create')}?po_id={po_id}")


# from decimal import Decimal
# from django.shortcuts import get_object_or_404, redirect
# from django.contrib import messages
# from django.urls import reverse
# from django.utils import timezone

def quality_management_receipt(request, po_id):

    po_obj = get_object_or_404(PurchaseOrderHeader, id=po_id)

    if request.method == "POST":

        item_errors = {}
        processed = 0

        #new
        document_number =GoodsMovementHeader.objects.filter(
            po_header=po_obj                  
        )
        prefix = "QM"
        gm_date_str = date.today().strftime("%Y-%m-%d")

        if prefix:
            increment_number = len(document_number) + 1 if len(document_number) > 0 else 1
            gm_code = f"{prefix}-{po_obj.code}-{increment_number}"

        gm_obj = GoodsMovementHeader.objects.create(
                code=gm_code,
                category='Quality Management',
                gm_date=gm_date_str,
                gm_posting_date=gm_date_str,
                po_header=po_obj
            )

        reference_number = generate_prv_number(po_obj, gm_obj, prefix)


        for item in po_obj.items.all():

            qty_str = request.POST.get(f"qty_being_received_{item.id}", "0")
            print("qty_str:",qty_str)
            inspected_str = request.POST.get(f"quality_already_inspected_{item.id}", "0")
            rejected_str = request.POST.get(f"quality_already_rejected_{item.id}", "0")
            qm_notes = request.POST.get(f"qm_notes_{item.id}", "")

            try:
                qty = Decimal(qty_str)
                inspected = Decimal(inspected_str)
                rejected = Decimal(rejected_str)
            except:
                item_errors[item.id] = ["Invalid numeric values"]
                continue

            # Basic validations
            if qty < 0:
                item_errors[item.id] = ["Quantity cannot be negative"]
                continue

            if rejected > inspected:
                item_errors[item.id] = ["Rejected qty cannot exceed inspected qty"]
                continue

            if qty == 0 and inspected == 0:
                continue

            try:
                history = process_goods_receipt(
                    po_item=item,
                    po_header=po_obj,
                    gm_date=timezone.now().date(),
                    gm_quantity=qty,
                    quality_already_rejected=rejected,
                    already_inspected_qty=inspected,
                    gm_type="Quality Management",
                    location=item.po_location,
                    sub_location=item.sub_location,
                    gm_text=qm_notes,
                    user=request.user,
                    reference_number=reference_number,
                    document_number=gm_obj
                )

                # ----------------------------
                # Save Rejection Breakdown
                # ----------------------------                
                rejection_codes_str = request.POST.get(f'rejection_code_{item.id}', '')                
                rejection_ids = [code.strip() for code in rejection_codes_str.split(',') if code.strip()]
                for code_id in rejection_ids:
                    PurchaseOrderHistoryRejection.objects.create(
                        po_history=history,
                        rejection_code_id=code_id
                        
                    )

                # ----------------------------
                # Save Single Document
                # ----------------------------
                file = request.FILES.get(f"qm_document_{item.id}")                

                if file:
                    PurchaseOrderHistoryDocument.objects.create(
                        po_history=history,
                        document=file
                        
                    )

                processed += 1

            except Exception as e:
                item_errors[item.id] = [str(e)]

        # ----------------------------
        # Update PO Header Status
        # ----------------------------
        statuses = [i.qty_inspection_status for i in po_obj.items.all()]

        if all(s == "CLOSED" for s in statuses):
            po_obj.qm_header_status = PurchaseOrderStatus.objects.get(name="CLOSED")
        elif all(s == "OPEN" for s in statuses):
            po_obj.qm_header_status = PurchaseOrderStatus.objects.get(name="OPEN")
        else:
            po_obj.qm_header_status = PurchaseOrderStatus.objects.get(name="PARTIAL")

        po_obj.save()

        if processed:
            messages.success(request, f"{processed} items processed successfully.")
        elif not item_errors:
            messages.info(request, "No quantities entered.")
        else:
            messages.warning(request, "Some rows contain errors.")

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


def quality_management_pdf(request,pk=None, prv_number='', report_type=''):
    
    try:
        # Get Purchase Order Header
        po_obj = get_object_or_404(PurchaseOrderHeader, pk=pk)
        
        # history_items = PurchaseOrderHistory.objects.filter(po_header_id=po_obj,reference_number=prv_number)
        history_items = PurchaseOrderHistory.objects.filter(
            po_header_id=po_obj,
            reference_number=prv_number
        ).order_by('updated_at')

        po = Purchase_Order.objects.get(po_number=po_obj.code)

        proc_obj = Procurement.objects.get(id=po.procurement_id)
    except ObjectDoesNotExist as e:
        raise ValueError(f"Required record not found: {e}")

    watermark_path = os.path.join(settings.BASE_DIR, 'static/default/img/priya-tr.png')

    #watermark_path = settings.STATIC_URL + 'default/priya-tr.png'

    if report_type == 'IRV':
        po_obj.name = f"{proc_obj.user.first_name} - {proc_obj.user.last_name}"
        template = 'inventory/inspection_receipt.html'
        filename = f'INSPECTION_CUM_RECEIPT_DOCUMENT_{prv_number}.pdf'
    else:
        po_obj.name = f"{proc_obj.user.first_name} - {proc_obj.user.last_name}"
        template = 'inventory/PRV.html'
        filename = f'PROVISION_CUM_RECEIPT_DOCUMENT_{prv_number}.pdf'

    context = {
        "po_obj": po_obj,
        "watermark_path": watermark_path,
        "prv_number":prv_number,
        "history_items": history_items
    }

    html = render_to_string(template, context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse(f'We had some errors <pre>{html}</pre>')

    return response


def purchase_order_list(request,pk=None):

    refs = PurchaseOrderHistory.objects.filter(
        po_header_id=pk,
        reference_number__isnull=False
    ).values_list('reference_number', flat=True)

    distinct_refs = list(set(refs))

    print(distinct_refs)
    return Response({"data": distinct_refs})


@api_view(['GET'])
def purchase_order_list(request, pk=None):
    logger.info("purchase_order_list API called")

    try:
        if not pk:
            return Response(
                {"message": "PO Header ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        distinct_refs = list(
            PurchaseOrderHistory.objects
            .filter(
                po_header_id=pk,
                reference_number__isnull=False
            )
            .exclude(reference_number='')
            .values_list('reference_number', flat=True)
            .distinct()
        )

        logger.info("purchase_order_list API executed successfully")

        return Response(
            {"data": list(set(distinct_refs))},
            status=status.HTTP_200_OK
        )

    except Exception as e:
        logger.exception("Error occurred in purchase_order_list API")
        return Response(
            {"message": "Something went wrong while fetching reference numbers"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa


def download_voucher_pdf(request):

    template = get_template("inventory/issue_voucher.html")

    html = template.render({
        "iv_no":"IV001",
        "iv_date":"01-03-2026"
    })

    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = 'attachment; filename="issue_voucher.pdf"'

    pisa.CreatePDF(html,dest=response)

    return response