from django.http import HttpResponse, Http404, HttpResponseRedirect
import datetime
from django.utils import timezone
import decimal
import re,random
from django.forms import ValidationError, model_to_dict
from django.shortcuts import get_object_or_404
from django.db.models import Max
from django.views import View
from django.shortcuts import render, redirect
from django.views import View
from django.urls import reverse
from requests import request
import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from collections import defaultdict
from ims.services.files import get_rejected_procurements
from .models import *
from django.contrib.auth.models import User
from django.views.generic import ListView
import pdb
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import *
from django.contrib.auth.decorators import login_required
from django.views.generic import DetailView
from django.contrib.auth.hashers import make_password
from django.views.generic import TemplateView
from django.contrib.auth import login, authenticate, logout
import decimal
from io import BytesIO
from reportlab.lib.pagesizes import letter # type: ignore
from reportlab.pdfgen import canvas # type: ignore
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
import json
from django.core.files.storage import FileSystemStorage
from django.db import IntegrityError, models
import pycountry
from django.db.models import Min
import pandas as pd
from datetime import datetime
import string
from datetime import date
import pdb
from django.db.models import Q
from vendor.models import Vendor,ProductVendor
from catalog.models import Product

def get_cst_data(procurement,cst_id, remarktype=None,particular_id = None, request=None):

    cstData = {}
    #pdb
    if procurement.is_delivered:
        # Work with vendor IDs from the start
        base_vendors = set(procurement.supplier.values_list('id', flat=True))

        if ModifiedPr.objects.filter(procurement=procurement).exists():
            modified_relation = ModifiedPr.objects.filter(procurement=procurement).latest('datetime')

            modified_vendors = set()
            removed_vendors = set()

            if modified_relation.modifiedpr:
                current_mod_vendors = set(modified_relation.modifiedpr.supplier.values_list('id', flat=True))

                modified_vendors.update(current_mod_vendors)
                removed_vendors.update(base_vendors - current_mod_vendors)

                base_vendors = modified_vendors
        else:
            base_vendors = set(procurement.supplier.values_list('id', flat=True))

        vendors_qs = Vendor.objects.filter(id__in=base_vendors).values('id', 'company_name1', 'email_1', 'code')

        vendor_list = [
            {
                'vendor_id': v['id'],
                'company_name': v['company_name1'],
                'email': v['email_1'],
                'vendor_code': v['code'],
                'selected': False
            } for v in vendors_qs
        ]

        #print(vendor_list)
        enquiry_number = "N/A"

    else:
        # Get the latest enquiry form for this procurement
        enquiryform = EnquiryFormPR.objects.filter(procure=procurement).order_by('-createddate').first()
        if not enquiryform:
            return cstData

        # Prepare vendor list
        quotations = VendorQuotations.objects.filter(eqno=enquiryform).select_related('vendors')
        vendors = {q.vendors for q in quotations}
        vendor_list = [
            {
                'vendor_id': vendor.id,
                'company_name': vendor.company_name1,
                'email': vendor.email_1,
                'vendor_code': vendor.code,
                'selected': VendorQuotationDetails.objects.filter(
                    vendor_quotation__eqno=enquiryform,
                    sources=vendor,
                ).exists()
            }
            for vendor in vendors
        ]

        enquiry_number = enquiryform.enquiryno

    # Fetch the latest CST (either original or modified), using the most recent StageProgress datetime
    cst_data = CompartiveStatementPR.objects.filter(
            id=cst_id,
            pro_id=procurement,
            #vendorquotationdetails__vendor_quotation__eqno__enquiryno=enquiry_number,
            cststate__remarktype__in=['CST', 'CST_Modified']
        ).first()
        

    saved_cst = {}
    indentor_selected_vendors = defaultdict(list)
    ra_selected_vendors = defaultdict(list)
    system_selected_vendors = defaultdict(list)

    if cst_data:
        vendor_quotation_entries = VendorQuotationDetails.objects.filter(cst=cst_data)
        for vq in vendor_quotation_entries:
            vid = vq.sources.id
            saved_cst.setdefault(vid, {'quantityrow': {},  'totalqty': {} ,'dollar_items': {},  'deliverytype': {} ,  'value': {} ,'system_gen_vend': {},  'terms': {} ,'deliverytimeline' : {}, 'delivery_unittypes' : {},'qty' : {} })

            # Aggregate items and dollar values
            for cstp in QuotationParticular.objects.filter(vendorquotationdetails=vq).distinct():
                if cstp.csparticular:
                    delivery_timelines = []
                    delivery_unittypes = []
                    delivery_qty = []
                    for qty in cstp.quantity.all():
                        if qty.deliverytimeline:
                            delivery_timelines.append(qty.deliverytimeline)
                        if qty.delivery_unittypes:
                            delivery_unittypes.append(qty.delivery_unittypes)
                        if qty.quantity:
                            delivery_qty.append(qty.quantity)
                    # You can store them as lists, or join them into comma-separated strings
                    saved_cst[vid]['deliverytimeline'][cstp.csparticular.id] = ','.join(delivery_timelines)
                    saved_cst[vid]['delivery_unittypes'][cstp.csparticular.id] = ','.join(delivery_unittypes)
                    saved_cst[vid]['qty'][cstp.csparticular.id] =delivery_qty
                    # Sum up all values and dollar_values for this particular
                    # total_value = sum(q.deliverytimeline or 0 for q in cstp.quantity.all())
                    # total_dollar = sum(q.dollar_value or 0 for q in cstp.quantity.all())
                    saved_cst[vid]['quantityrow'][cstp.csparticular.id] =""
                    saved_cst[vid]['totalqty'][cstp.csparticular.id] = cstp.totalqty
                    saved_cst[vid]['dollar_items'][cstp.csparticular.id] = cstp.dollar_value
                    saved_cst[vid]['deliverytype'][cstp.csparticular.id] = cstp.deliverytype.delivery_name
                    saved_cst[vid]['value'][cstp.csparticular.id] = cstp.value
                    saved_cst[vid]['system_gen_vend'][cstp.csparticular.id] = cstp.system_choosen_vendor

            # Capture vendor terms
            vo = vq.validityoffer
            validityoffer = vo.isoformat() if isinstance(vo, datetime) else (vo or '')
            saved_cst[vid]['terms'] = {
                'quotation_reference': vq.quotation_reference or '',
                'validityoffer': validityoffer,
                'discount': vq.discount or '',
                # 'deliverytimeline': vq.deliverytimeline or '',
                # 'delivery_unittypes': vq.delivery_unittypes or '',
                'gst': vq.gst or '',
                'deliveryterms': vq.deliveryterms or '',
                'paymentterms': vq.paymentterms or '',
                'packaging_charges': vq.packaging_charges or '',
                'insurance_charges': vq.insurance_charges or '',
                'customs_duty': vq.customs_duty or '',
                'coc': vq.coc,
                'material_test_report': vq.material_test_report,
                # 'additional_info': vq.additional_info or '',
            }

        # Determine selected vendors per particular item
        all_vqd = VendorQuotationDetails.objects.filter(cst=cst_data).prefetch_related('particular', 'sources')
        for detail in all_vqd:
            for qp in detail.particular.all():
                if qp.csparticular:
                    pid = qp.csparticular.id
                    info = {
                        'id': pid,
                        'vendor_id': detail.sources.id,
                        'company_name': detail.sources.company_name1,
                        'quotation_reference': detail.quotation_reference,
                        'negotiation': qp.ra_negotiation,
                        'indentor_negotiation': qp.indentor_negotiation,
                    }
                    if qp.indentor_choosen_vendor:
                        indentor_selected_vendors[pid].append(info)
                    if qp.ra_choosen_vendor:
                        ra_selected_vendors[pid].append(info)
                    if qp.system_choosen_vendor:
                        system_selected_vendors[pid].append(info)
    # Prepare particulars list from latest modified procurement or original
    latest_mod_pr = ModifiedPr.objects.filter(procurement=procurement).order_by('-datetime').first()
    base_pr = latest_mod_pr.modifiedpr if latest_mod_pr and latest_mod_pr.modifiedpr else procurement
    particulars_list_cst = [
        {
            'id': p.id,
            'item_name': p.item_name,
            'partno': p.partno,
            'make': p.make,
            'item_specification': p.item_specification,
            'reasons_document': p.reasons_document.url if p.reasons_document else None,
            'spec_document': p.spec_document.url if p.spec_document else None,
            'estimated_value': p.estimatedvalue,
            'reasons_for_procurement': p.reasons_for_procurement,
            'total_qty_required': p.total_qty_required,
        }
        for p in base_pr.particular.all()
    ]
    
    particulars_list_cst = list({p['id']: p for p in particulars_list_cst}.values())

    # Handle filtering by particular_id if needed
    if particular_id is None and request:
        try:
            particular_id = int(request.POST.get('particular_id', ''))
        except (TypeError, ValueError):
            particular_id = None

    indentor_for_particular = indentor_selected_vendors.get(particular_id, []) if particular_id else []
    ra_for_particular = ra_selected_vendors.get(particular_id, []) if particular_id else []
    system_for_particular = system_selected_vendors.get(particular_id, []) if particular_id else []

    # User and payment tracking info
    user = getattr(procurement, 'user', None)
    userData = {
        'username': user.username, 'full_name': f"{user.first_name} {user.last_name}",
        'first_name': user.first_name, 'last_name': user.last_name
    } if user else None

    installments = []
    payData_id = [i.id for i in cst_data.payment_invest.all()]
    for inst in PaymentTracking.objects.filter(payment__procurement=procurement,payment_id__in=payData_id).select_related('payment', 'submitted_by').prefetch_related('payment_file'):
        installments.append({
            'installment_name': inst.payment.installmentname,
            'installment_date': str(inst.installment_date or ''),
            'payment_percentage': float(inst.payment_percentage or 0.0),
            'payment_events': inst.payment_events,
        })
    cst_dict = model_to_dict(
        cst_data, 
        fields=['id', 'pro_id', 'csuser','cststate', 'send_to', 'additional_info']
    )

    # Assemble final data
    cstData = {
        'cs_data':cst_dict,
        'enquiryNo': enquiry_number,
        'projectName': procurement.project.name if getattr(procurement, 'project', None) else '',
        'userData': userData,
        'vendors': vendor_list,
        'particulars': particulars_list_cst,
        'saved_cst': saved_cst,
        'indentor_selected_vendors': dict(indentor_selected_vendors),
        'ra_selected_vendors': dict(ra_selected_vendors),
        'system_selected_vendors': dict(system_selected_vendors),
        'indentor_vendors_for_particular': indentor_for_particular,
        'ra_vendors_for_particular': ra_for_particular,
        'system_vendors_for_particular': system_for_particular,
        'installments': installments,
        # 'additionalInfo': (
        #     vendor_quotation_entries[0].additional_info 
        #     if latest_cst and vendor_quotation_entries else ''
        # ),
        
    }

    return cstData


def get_dpo_data(procurement):
    dpo_original_data = []
    dpo_modified_data = []
    # #pdb

    dpo_qs = DPO.objects.filter(procurement=procurement)
    #print(f"Total DPO records found: {dpo_qs.count()}")

    for dpo in dpo_qs:
        vendor = dpo.sources

        vendor_data = [{
            'vendor_id': vendor.code,
            # 'vendor_name': vendor.vendor_name,
            'email': vendor.email_1,
            'phone_number': vendor.phone_number_1,
            # 'gst_number': vendor.gst_number,
            'address': vendor.building_name,
            # 'tin_number': vendor.tin_number,
            'state': vendor.state,
            # 'city': vendor.city,
            'pincode': vendor.zipcode,
            'company_name': vendor.company_name1,
            # 'country': vendor.country,
        }] if vendor else []

        particular_data_dpo = []
        for particular in dpo.particular.all():
            negotiation = particular.negotiation

            particular_data_dpo.append({
                'description': particular.description or '',
                'quantity_dpo': particular.quantity_dpo or '',
                'partno': particular.partno_dpo or '',
                'modelno': particular.modelno_dpo or '',
                'unitname': str(particular.units_dpo) if particular.units_dpo else particular.unit_display or '',
                'unit_price_dpo': str(particular.unit_price_dpo or ''),
                'total_value': str(particular.total_value or ''),
                'negotiated_value': negotiation.negotiated_price if negotiation else '',
                'negotiated_tax': negotiation.negotiated_taxes if negotiation else '',
            })

        remarktype = dpo.dpostage.remarktype if dpo.dpostage else None

        dpo_entry = {
            'dpoid': dpo.dpoid,
            'date': dpo.date,
            'total_value': float(sum(p.total_value for p in dpo.particular.all())),
            'discount': float(dpo.discount),
            'packingcharges': float(dpo.packingcharges),
            'gst_percentage': float(dpo.gst_percentage) if dpo.gst_percentage is not None else None,
            'gst_value': float(dpo.gst_value) if dpo.gst_value is not None else None,
            'grand_total': float(dpo.grand_total),
            'termcond': dpo.termcond,
            'gentermcond': dpo.gentermcond,
            'payment_terms': dpo.payment_terms,
            'quotation_reference': dpo.quotation_refrence,
            'delivery_weeks': dpo.delivery_weeks,
            'warranty_period': dpo.warranty_period,
            'billing_address_1': dpo.billing_address_1,
            'delivery_address_2': dpo.delivery_address_2,
            'poid': dpo.poid,
            'particulars': particular_data_dpo,
            'vendor_data': vendor_data,
            'form_type': 'import' if procurement.import_indigenous and procurement.import_indigenous.source_code == "02" else 'indigenous',
            'dpostage': {
                'stageid': dpo.dpostage.id,
                'stage': dpo.dpostage.stagename.stage if dpo.dpostage and dpo.dpostage.stagename else None,
                'remarktype': remarktype,
                'remarks': dpo.dpostage.remarks if dpo.dpostage else None,
                'user': dpo.dpostage.user.get_full_name() if dpo.dpostage and dpo.dpostage.user else None,
                'datetime': dpo.dpostage.datetime if dpo.dpostage else None
            } if dpo.dpostage else None,
        }

        if remarktype == 'DPO':
            dpo_original_data.append(dpo_entry)
        elif remarktype == 'DPO_Modified':
            dpo_modified_data.append(dpo_entry)

    return dpo_original_data, dpo_modified_data

def get_current_financial_year():
    """Returns financial year in format '2024-2025'."""
    today = date.today()
    if today.month >= 4:
        return f"{today.year}-{today.year + 1}"
    else:
        return f"{today.year - 1}-{today.year}"


        
def prepare_enquiry_data(enquiry_forms):
    enquiry_data = []
    # #pdb
    for enquiry in enquiry_forms:
        enquiry_info = {
            "enquiry_no": enquiry.enquiryno,
            "due_date": enquiry.dateddue,
            "terms_conditions": enquiry.en_term_cond,
            "delivery_dates": [],
            "subject": enquiry.subject,
            "createddate": enquiry.createddate,
            "remarktype": enquiry.stageprogress.remarktype if enquiry.stageprogress else '',
            "stage_id": enquiry.stageprogress.id if enquiry.stageprogress else None,
            "suppliers": [] , # <-- Add this to hold suppliers info
             "latest_particulars": []
        }

        procurement_id = enquiry.procure.procurement_id  # assuming each EnquiryFormPR has 'procure' FK
        current_procurement = Procurement.objects.get(procurement_id=procurement_id)
        latest_procurement = current_procurement

        # Traverse ModifiedPr to get the latest
        while True:
            next_modified_link = ModifiedPr.objects.filter(procurement=latest_procurement).order_by('-datetime').first()
            if not next_modified_link or not next_modified_link.modifiedpr:
                break
            latest_procurement = next_modified_link.modifiedpr

        # Get particular details from latest procurement
        latest_particulars = latest_procurement.particular.all()
        for p in latest_particulars:
            enquiry_info["latest_particulars"].append({
                "id": p.id,
                "description": p.item_name,
                "unitname": p.unitname.unit if p.unitname else None,
                "partno": p.partno,
                "make": p.make,
                "estimated_value": p.estimatedvalue,
                "reasons_for_procurement": p.reasons_for_procurement,
                "total_qty_required": p.total_qty_required,
                "items_to_be_positioned_by": [
                    {
                        "id": dq.id,
                        "expected_date": dq.expected_date,
                        "quantity": dq.quantity,
                    } for dq in p.datequantity.all()
                ],
                "item_specification": p.item_specification,
                "spec_document": p.spec_document.url if p.spec_document else None,
                "reasons_document": p.reasons_document.url if p.reasons_document else None,
                "quot_file": p.Quotation_upload.url if p.Quotation_upload else None,
                "delivery_name": p.delivery.delivery_name if p.delivery else None,
            })

        # Add supplier info if enquirysuppliers exists
        if enquiry.enquirysuppliers:
            suppliers_qs = enquiry.enquirysuppliers.suppliers.all()
            enquiry_info["suppliers"] = [
                {
                    "id": supplier.id,
                    "company_name": supplier.company_name,
                    "email": supplier.email,
                    # Add any other fields you want to send
                }
                for supplier in suppliers_qs
            ]

        delivery_dates_qs = enquiry.delivery_date.select_related(
            'en_particular', 'delivery_type'
        ).prefetch_related('en_quantity').all()

        for delivery_date in delivery_dates_qs:
            quantities = list(delivery_date.en_quantity.values('quantity', 'en_expected_date'))

            delivery_info = {
                "particular_id": delivery_date.en_particular.id if delivery_date.en_particular else None,
                "particular_name": delivery_date.en_particular.item_name if delivery_date.en_particular else None,
                "total_quantity": delivery_date.total_quantity,
                "delivery_type_id": delivery_date.delivery_type.id if delivery_date.delivery_type else None,
                "delivery_type_name": delivery_date.delivery_type.delivery_name if delivery_date.delivery_type else None,
                "quantities": quantities,
            }
            enquiry_info["delivery_dates"].append(delivery_info)

        enquiry_data.append(enquiry_info)

    return enquiry_data

class Return_PR(View):
    @method_decorator(csrf_exempt)
    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, *args, **kwargs):
        return super(Return_PR, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        user = request.user
        rejected_prs = get_rejected_procurements(request,user)

        delivery_name = list(Delivery.objects.all().values("id", "delivery_name"))
        tender_type = list(TenderType.objects.all().values("tender_type", "tender_code"))
        suppliers = list(Vendor.objects.values("company_name1", "code"))
        units_data = Units.objects.all().values('id', 'unit')
        pr_choices_list = [{"value": key, "label": value} for key, value in Procurement.pr_choices]

        return render(request, "ims/pr_reject.html", {
            "rejected_prs": rejected_prs,
            "delivery_name": delivery_name,
            'units_data': json.dumps(list(units_data)),
            "suppliers": json.dumps(suppliers),
            "tender_type": tender_type,
            "pr_choices": json.dumps(pr_choices_list),
        })

    # def get(self, request, *args, **kwargs):
    #     try:
    #         # Get all procurements currently in stage1 due to a rejection by the current user
    #         stage1_rejections = StageProgress.objects.filter(
    #             rejectstage__stage="stage1",
    #             remarktype="Reject",
    #             rejectuser=request.user
    #         ).values("procurement_id__procurement_id", "stagename__stage", "rejectstage__stage")

    #         # Filter procurements that were returned to stage1 from a higher stage (stage2 to stage5)
    #         returned_to_stage1 = [
    #             entry["procurement_id__procurement_id"]
    #             for entry in stage1_rejections
    #             if entry["stagename__stage"] in ["stage2", "stage3", "stage4", "stage5"]
    #         ]

    #         # Remove duplicates
    #         returned_to_stage1 = list(set(returned_to_stage1))

    #         # Get rejected procurement records
    #         rejected_prs = Procurement.objects.filter(procurement_id__in=returned_to_stage1).annotate(
    #             latest_reject_datetime=Max(
    #                 'prid__datetime',
    #                 filter=Q(
    #                     prid__remarktype='Reject',
    #                     prid__rejectuser=request.user,
    #                     prid__rejectstage__stage='stage1'
    #                 )
    #             )
    #         ).order_by('-latest_reject_datetime', '-id')

    #         # Mark if action can be performed
    #         for procurement in rejected_prs:
    #             # Get last StageProgress entry for this procurement
    #             last_stage = (
    #                 StageProgress.objects
    #                 .filter(procurement_id__procurement_id=procurement.procurement_id)
    #                 .order_by('-datetime')
    #                 .first()
    #             )

    #             if (
    #                 last_stage
    #                 and last_stage.remarktype == "Reject"
    #                 and last_stage.stagename.stage <= "stage5"  # Assuming 'stage' is a string like "stage1", "stage2", etc.
    #                 and last_stage.rejectuser == request.user
    #             ):
    #                 procurement.action_performed = True
    #             else:
    #                 procurement.action_performed = False

    #     except Exception as e:
    #         #print("Error:", e)
    #         rejected_prs = []

    #     delivery_name = list(Delivery.objects.all().values("id", "delivery_name"))
    #     tender_type = list(TenderType.objects.all().values("tender_type", "tender_code"))
    #     suppliers = list(Vendor.objects.values("company_name", "vendor_id"))
    #     units_data = Units.objects.all().values('id', 'unit')

    #     return render(request, "pr_reject.html", {
    #         "rejected_prs": rejected_prs,
    #         "delivery_name": delivery_name,
    #         'units_data': json.dumps(list(units_data)),
    #         "suppliers": json.dumps(suppliers),
    #         "tender_type": tender_type
    #     })

    def post(self, request, *args, **kwargs):
        # #pdb
        data_list = []
        #pdb
        data_dict = json.loads(request.body.decode('utf-8'))
        pro_id = data_dict.get('selected_pr')
        mainprocurement = Procurement.objects.get(procurement_id=pro_id)
        procurement = Procurement.objects.get(procurement_id=pro_id)
        
        
       
 
 
        # Get all modified procurement IDs for the current procurement
        modified_procurement_ids = ModifiedPr.objects.filter(
            procurement=procurement
        ).values_list('modifiedpr__modifiedpr_id', flat=True)
 
        procurements = Procurement.objects.select_related(
            'import_indigenous', 'tender_type', 'procurement_type', 'branch',
            'department', 'project', 'user'
        ).prefetch_related('supplier', 'particular').filter(
            Q(procurement_id=pro_id) | Q(modifiedpr_id__in=modified_procurement_ids)
        ).order_by('datetime')
        user=request.user
        # #print(user)
        enquiry_suppliers = EnquirySupplierPR.objects.filter(procure=procurement)
       
        enquiry_vendors = set()
        for enquiry in enquiry_suppliers:
            enquiry_vendors.update(enquiry.suppliers.all())
        
        # Format vendor data to send to frontend
        enquiry_vendor_data = [
            {
                "vendid": vendor.id,
                "vendor_id": vendor.vendor_id,
                "company_name": vendor.company_name1,
                "vendor_email": vendor.email_1,
            }
            for vendor in enquiry_vendors
        ]
        duedate = list(EnquiryFormPR.objects.filter(procure=procurement).values('dateddue'))
        procurement_list = []  # For original procurement data
        modified_procurement_list = []  # For modified procurement data
 
   
 
 
        for procurement in procurements:
            procurement_data = {
            'procurement_id': procurement.procurement_id,
            'modifiedpr_id': procurement.modifiedpr_id,
            'earlier_procurement_details': procurement.earlier_procurement_details,
            'import_indigenous': str(procurement.import_indigenous),
            'tender_type': str(procurement.tender_type),
            'procurement_type': str(procurement.procurement_type),
            'branch': str(procurement.branch),
            'department': str(procurement.department),
            'project': str(procurement.project),
            'user': str(procurement.user.username) if procurement.user else 'N/A',
            'user_first_name': procurement.user.first_name if procurement.user else 'N/A',
            'user_last_name': procurement.user.last_name if procurement.user else 'N/A',
            'user_department': procurement.user.userreg.user_dept.dept_name if procurement.user and procurement.user.userreg and procurement.user.userreg.user_dept else 'N/A',
            'quality_certificates_required': procurement.quality_certificates_required,
            'material_to_confirm_to_standard': procurement.material_to_confirm_to_standard,
            'quality_document': str(procurement.quality_document),
            'cancellation': procurement.cancellation,
            'modificationpr': procurement.modificationpr,
            'datetime': procurement.datetime,
            'is_draft': procurement.is_draft,
            'is_delivered':procurement.is_delivered,
            'category_events':procurement.category_events,
            'pr_events':procurement.pr_events,
            'quality_document_url': procurement.quality_document.url if procurement.quality_document else None,

            }
            # #print(procurement_data)
 
            # #pdb
 
            procurement_data['suppliers'] = [
                {
                    'vendor_id': supplier.code,
                   
                    'email': supplier.email_1,
                    'company_name':supplier.company_name1,
                    'phone_number': supplier.phone_number_1
                } for supplier in procurement.supplier.all()
            ]
            
            procurement_data['particulars'] = [
                {
                    'particular_id':particular.id,
                    'item_name': particular.item_name,
                    'item_specification': particular.item_specification,
                    'total_qty_required': particular.total_qty_required,
                    'estimatedvalue': particular.estimatedvalue,
                    'make': particular.make,
                    'partno': particular.partno,
                    'item_specification':particular.item_specification,
                    'spec_document': particular.spec_document.url if particular.spec_document else None,
                    'reasons_document': particular.reasons_document.url if particular.reasons_document else '',
                    'reasons_for_procurement': particular.reasons_for_procurement,
                    'quantity': [
                        {
                            'quantity': qty.quantity,
                            'expected_date': str(qty.expected_date)
                        } for qty in particular.datequantity.all()
                    ],
                    'delivery_data': particular.delivery.delivery_name if particular.delivery else 'N/A',
                    'unit': particular.unitname.unit if particular.unitname else 'N/A',
                    'quot_file': particular.Quotation_upload.url if particular.Quotation_upload else None,
                } for particular in procurement.particular.all()
            ]
           
            for particular in procurement_data['particulars']:
                print(f"  Spec Document: {particular['spec_document']}")
            # Segregate into original and modified procurements based on `modifiedpr_id`
            if procurement.modifiedpr_id:
                modified_procurement_list.append(procurement_data)  # Add to modified list
            else:
                procurement_list.append(procurement_data)  # Add to original procurement list
        # #print(procurement_data)
        # Prepare the response data
        procurement_df = pd.DataFrame(procurement_list).astype(str)
        Procurement_details = procurement_df.to_dict(orient='records')
 
        # Fetch stage progress remarks
        proc_notes_records = StageProgress.objects.select_related('procurement_id', 'stagename', 'user').filter(
            procurement_id=procurement
        )

        stages_list = [
            {
                'stageid':stage.id,
                'stage': stage.stagename.stage,
                'remarktype': stage.remarktype,
                'remarks': stage.remarks,
                #  'user':  stage.user.first_name if stage.user else None,
                    'user': {
                    'first_name': stage.user.first_name if stage.user else None,
                    'last_name': stage.user.last_name if stage.user else None,
                },
                'userid':  stage.user.username if stage.user else None,
                'user_role': [i.role for i in stage.user.userreg.role.all()],
                'userdept': stage.user.userreg.user_dept.dept_name if stage.user and stage.user.userreg and stage.user.userreg.user_dept else None,
                'datetime': stage.datetime,
                'user_role': [i.role for i in stage.user.userreg.role.all()],
                'modified_prno':stage.modified_id.modifiedpr_id if stage.modified_id else None,
                'attachment': stage.attachment.url if stage.attachment else None,
                'forwarded_to': stage.forwarded_to.username if stage.forwarded_to else None,
                'forwarded_to_name': (
                    f"{stage.forwarded_to.first_name} {stage.forwarded_to.last_name}".strip()
                    if stage.forwarded_to else None
                ),
                'reject_to': stage.rejectuser.username if stage.rejectuser else None,
                'reject_to_name': (
                    f"{stage.rejectuser.first_name} {stage.rejectuser.last_name}".strip()
                    if stage.rejectuser else None
                ),
                'vendor': {
                    'vendor_id': stage.vendors.vendor_id if stage.vendors else None,
                    'vendor_name': stage.vendors.company_name1 if stage.vendors else None,
                }
            }
            for stage in StageProgress.objects.filter(procurement_id=Procurement.objects.get(procurement_id=pro_id)).exclude(
                    # Q(stagename__stage='stage1', remarktype="PR_Raised") |
                    ## Q(stagename__stage='stage6', remarktype="Enquiry Generated")|
                    # Q(stagename__stage='stage8', remarktype="Negotiation")
                )
        ]
   
        
        checkmsg = StageProgress.objects.filter(
            procurement_id__procurement_id=Procurement.objects.get(procurement_id=pro_id).procurement_id
        ).order_by('-datetime').first()
        #pdb
       
        if checkmsg.rejectstage and checkmsg.rejectstage.stage == "stage1":
            # --------- Final result ---------
            showbutton = True
        else:
            showbutton = False

        # #pdb
        source_type = ''
        if procurement.import_indigenous and procurement.import_indigenous.source_type:
            source_type = procurement.import_indigenous.source_type
        
        
        cst_generated_data = []
        #cst 
        try:
            cst_generated = CompartiveStatementPR.objects.get(
                pro_id=mainprocurement.id,
                cststate__remarktype='CST'
            )
            if(cst_generated):
                cst_generated_data = get_cst_data(mainprocurement,cst_generated.id, remarktype='CST')
        except:
            print("no cst till")
        
        cst_modified = CompartiveStatementPR.objects.filter(
            pro_id=mainprocurement.id,
            cststate__remarktype='CST_Modified'
        )

        cst_modified_data = [
            get_cst_data(mainprocurement, obj.id, remarktype='CST_Modified')
            for obj in cst_modified
        ] if cst_modified.exists() else []

       
        dpo_original_data, dpo_modified_data = get_dpo_data(mainprocurement)
                # Step 1: Try to get modified particulars from ModifiedPr
        #pdb
        modified_particular_ids = []
        modified_procurement_ids = []

        try:
            modified_procurement_ids = list(
                ModifiedPr.objects.filter(procurement=procurement).values_list('modifiedpr__modifiedpr_id', flat=True)
            )
            #print("Modified procurement IDs:", modified_procurement_ids)

            if modified_procurement_ids:
                modified_particular_ids = list(
                    Particular.objects.filter(procurement__modifiedpr_id__in=modified_procurement_ids).values_list('id', flat=True)
                )
        except Exception as e:
            print(f"Error while checking for modified PRs: {e}")

        # Step 2: Decide which particulars to use
        if modified_particular_ids:
            #print("Using modified particulars for negotiation")
            particular_qs = Particular.objects.filter(id__in=modified_particular_ids)
        else:
            #print("Using original procurement particulars for negotiation")
            particular_qs = procurement.particular.all()

        # Step 3: Extract negotiation data
        negotiation_data = []

        for particular in particular_qs:
            quotation_particulars = QuotationParticular.objects.filter(csparticular=particular)

            all_vqds = {}

            for qp in quotation_particulars:
                negotiations = Negotiation.objects.filter(quoted_vendors=qp)
                vqd = VendorQuotationDetails.objects.filter(particular=qp).first()
                all_vqds[qp.id] = vqd

                for negotiation in negotiations:
                    stage_progress_qs = StageProgress.objects.filter(
                        nego_quota_particular=negotiation
                    ).filter(
                        Q(remarktype='Negotiation') |
                        Q(remarktype='Negotiation_approval') |
                        Q(remarktype='Negotiation_Modified') |
                        Q(remarktype='Negotiation_return') |
                        Q(remarktype='Approval') |
                        Q(remarktype='Reject')
                    )

                    selected_vqd = all_vqds.get(qp.id)

                    for stage_progress in stage_progress_qs:
                        qp_for_negotiation = negotiation.quoted_vendors
                        related_csparticular = qp_for_negotiation.csparticular if qp_for_negotiation else None
                        selected_vqd = all_vqds.get(qp_for_negotiation.id) if qp_for_negotiation else None
                        print("Negotiation vendors:", negotiation.vendors)
                        ##pdb
                        if negotiation.vendors:
                            print("")
                        else:
                            print("")

                        negotiation_data.append({
                            'id': stage_progress.id,
                            'stage_datetime': stage_progress.datetime.isoformat() if stage_progress and stage_progress.datetime else None,
                            'stage_remarktype': stage_progress.remarktype if stage_progress else None,
                            'stage_remarks': stage_progress.remarks if stage_progress else None,
                            'particular_id': related_csparticular.id if related_csparticular else None,
                            'particular_name': related_csparticular.item_name if related_csparticular else None,
                            'quoted_vendors_id': qp.id,
                            'vendor_name': negotiation.vendors.company_name1 if negotiation.vendors else (selected_vqd.sources.company_name1 if selected_vqd and selected_vqd.sources else None),
                            'quoted_product': negotiation.quoted_product,
                            'quoted_quantity': negotiation.quoted_quantity,
                            'quoted_price': negotiation.quoted_price,
                            'quoted_taxes': negotiation.quoted_taxes,
                            'quoted_warranty': negotiation.quoted_warranty,
                            'quoted_paymentterms': negotiation.quoted_paymentterms,
                            'quoteddeliveryschedule': negotiation.quoteddeliveryschedule,
                            'quoteddeliveryterms': negotiation.quoteddeliveryterms,
                            'quoted_aftersalessupport': negotiation.quoted_aftersalessupport,
                            'quoted_documentation_url': negotiation.quoted_documentation.url if negotiation.quoted_documentation else '',
                            'quoted_memberspresent': negotiation.quoted_memberspresent,
                            'quoted_anyotherpointnotcovered': negotiation.quoted_anyotherpointnotcovered,
                            'negotiated_product': negotiation.negotiated_product,
                            'negotiated_quantity': negotiation.negotiated_quantity,
                            'negotiated_price': negotiation.negotiated_price,
                            'negotiated_taxes': negotiation.negotiated_taxes,
                            'negotiated_warranty': negotiation.negotiated_warranty,
                            'negotiated_paymentterms': negotiation.negotiated_paymentterms,
                            'negotiateddeliveryschedule': negotiation.negotiateddeliveryschedule,
                            'negotiateddeliveryterms': negotiation.negotiateddeliveryterms,
                            'negotiated_aftersalessupport': negotiation.negotiated_aftersalessupport,
                            'negotiated_documentation_url': negotiation.negotiated_documentation.url if negotiation.negotiated_documentation else '',
                            'negotiated_memberspresent': negotiation.negotiated_memberspresent,
                            'negotiated_anyotherpointnotcovered': negotiation.negotiated_anyotherpointnotcovered,
                            'rep_from_finance': negotiation.rep_from_finance,
                            'head_imm': negotiation.head_imm,
                            'director_project_delivery': negotiation.director_project_delivery,
                            'chairman_pnc': negotiation.chairman_pnc,
                            'quotation_ref_date': negotiation.quotation_ref_date,
                            'datetime': negotiation.datetime.isoformat() if negotiation.datetime else None,
                            'submitted_by': negotiation.submitted_by.get_full_name() if negotiation.submitted_by else None,
                        })


       
        #for enq 
        enquiry_supplier_pr = EnquirySupplierPR.objects.filter(procure=mainprocurement).first()
   
        suppliers = enquiry_supplier_pr.suppliers.all() if enquiry_supplier_pr else []

        # Supplier names and details
        supplier_names = [supplier.company_name1 for supplier in suppliers]

        procument_obj = Procurement.objects.filter(procurement_id=pro_id).first()

        pro_supplier = procument_obj.supplier.all() if procument_obj else []

        # Supplier names and details
        supplier_pro = [supplier.company_name1 for supplier in pro_supplier]
        supplier_obj = list(pro_supplier)+list(suppliers)

        supplier_details = [
            {
                "mail": supplier.email_1 or "N/A",
                "company_name": supplier.company_name1 or "N/A"
            }
            for supplier in supplier_obj
        ]
        enquiry_generated_forms = EnquiryFormPR.objects.filter(
                procure=mainprocurement,
                stageprogress__remarktype='Enquiry Generated'
            )
    

            # Enquiries linked to remarktype 'Enquiry_Modified'
        enquiry_modified_forms = EnquiryFormPR.objects.filter(
                procure=mainprocurement,
                stageprogress__remarktype='Enquiry_Modified'
            )

        enquiry_generated_data = prepare_enquiry_data(enquiry_generated_forms)
        enquiry_modified_data = prepare_enquiry_data(enquiry_modified_forms)
            # data_list.append(cstData)
            # #print("data list here: ", data_list)

        #pdb
        project = procurement.project
        current_remaining_budget = 0

        if project:
            
            budget = procurement.budget or mainprocurement.budget
            financial_year = budget.financial_year if budget else None

            if financial_year:
                try:
                    budget_allocation = BudgetAllocation.objects.get(
                        project=project,
                        financial_year=financial_year
                    )
                    current_remaining_budget = budget_allocation.remaining_budget
                except BudgetAllocation.DoesNotExist:
                    print(f"No budget allocation found for project '{project.name}' in financial year '{financial_year}'.")
            else:
                print("")
        else:
            print("")

 
        # Append the modify page data
       
        data_list.append({
            'original_procurement_details': procurement_list,  # Original procurement data
            'modified_procurement_details': modified_procurement_list,
            'showbutton': showbutton,  # Modified procurement data
            'remaining_budget': current_remaining_budget,
            'enquiry_vendor_data':enquiry_vendor_data,
            'date':duedate,
            'source_type': source_type,
            'dpo_original_data': dpo_original_data,
            'dpo_modified_data': dpo_modified_data,
            "enquirydata": enquiry_generated_data,
            "enquiry_modified": enquiry_modified_data,
            'cst_generated': cst_generated_data,
            'cst_modified': cst_modified_data,
            'suppliers': supplier_names,
            'supplier_details':supplier_details,
            'negotiation_data':negotiation_data,
            'stages': stages_list
        })


        # Append stage progress remarks
        data_list.append(stages_list)


        

        return JsonResponse(data_list, safe=False, status=200)
      
 
 
 