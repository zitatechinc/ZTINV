from django.shortcuts import render
from core.views import ProjectHeaderBaseCRUDView, VoucherHeaderBaseCRUDView, BOMHeaderBaseCRUDView, BaseCRUDView,BOMCRUDView,ProjectBaseCRUDView,ProjectIssueVoucherCRUDView
from .models import ProjectHeader, ProjectComponent, BOMHeader, BOMItem,BOMAttachments, VoucherHeader, VoucherComponent
from .forms import ProjectSearchModelForm, BOMSearchModelForm, BOMHeaderModelForm, ProjectHeaderModelForm, ProjectComponentModelForm, VoucherSearchModelForm, BOMItemModelForm,BOMAttachmentsModelForm
from rest_framework.response import Response
from rest_framework.decorators import api_view
from ims.models import Project, BudgetAllocation
from inventory.models import Inventory,GoodsMovementHeader
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.conf import settings
import os
from xhtml2pdf import pisa # pdf download
import logging
logger = logging.getLogger(__name__)
logger = logging.getLogger('console')


# Create your views here.

class ProjectSearchView(ProjectHeaderBaseCRUDView):
    model = ProjectHeader
    form_class = ProjectSearchModelForm

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

def project_header_receipt(request, po_id):
    po_obj = get_object_or_404(ProjectHeader, id=po_id)
    
    if request.method == "POST":
        item_errors = {}
        processed = 0
        ht_items_list = []
        for item in po_obj.items.all():      

            # Collect row-specific errors
            row_errors = []  
            
            # Process valid rows
            gm_date_str = date.today().strftime("%Y-%m-%d")
            data = {
                "po_header": po_obj,
                "po_item" : item,
                # gm_date=gm_date_str,
                # location=item.po_location,
                # sub_location=item.sub_location,
                # user=request.user
            }
            processed += 1
            ht_items_list.append(item.pk)

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

    return redirect(f"{reverse('project-search-create')}?po_id={po_id}")

@api_view(['GET'])
def project_list(request):
    logger.info("project_list API called")
    try:
        projects = Project.objects.all()
        logger.debug(f"Total projects fetched: {projects.count()}")  

        data = []
        for i in projects:
            data.append({
                "id": i.id,
                "code": i.project_id,
                "name" : i.name
            })

        logger.info("project_list API executed successfully")
        return Response({"data": data})

    except Exception as e:
        logger.exception("Error occurred in project_list API")
        return Response(
            {"message": "Something went wrong while fetching projects"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        

class BOMSearchView(BOMHeaderBaseCRUDView):
    model = BOMHeader
    form_class = BOMSearchModelForm
    FieldList = (
        ('code', 'BOM Code'),
        ('project', 'Project Header'),
        ('updated_at', 'Updated at'),
    )
    
    def get_extra_context(self):
        
        return {
            
        }

def bom_header_receipt(request, po_id):
    po_obj = get_object_or_404(BOMHeader, id=po_id)

    if request.method == "POST":
        item_errors = {}
        processed = 0
        ht_items_list = []
        for item in po_obj.items.all():      

            # Collect row-specific errors
            row_errors = []  
            
            # Process valid rows
            gm_date_str = date.today().strftime("%Y-%m-%d")
            data = {
                "po_header": po_obj,
                "po_item" : item,
            }
            processed += 1
            ht_items_list.append(item.pk)

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

    return redirect(f"{reverse('bom-create')}?po_id={po_id}")


# ---------------- ProjectHeader CRUD ----------------
class ProjectHeaderCrudView(BaseCRUDView):
    model = ProjectHeader
    form_class = ProjectHeaderModelForm
    FieldList = (
        ('project__project_id', 'Project Code'),
        ('project__name', 'Project Name'),
        ('customer__company_name1', 'Customer'),
        ('location__name', 'Location'),
        ('updated_at', 'Updated at'),
    )

    def get_extra_context(self):
        return {
            'page_title': 'Project Header',
            'model_name': 'ProjectHeader',
        }

# ---------------- ProjectComponent CRUD ----------------
class ProjectComponentCrudView(ProjectBaseCRUDView):
    model = ProjectComponent
    form_class = ProjectComponentModelForm
    FieldList = (
        ('code', 'Component Code'),
        ('component_type', 'Component Type'),
        ('project', 'Project'),
        ('bom', 'BOM'),
        ('product', 'Product'),
        ('service', 'Service'),
        ('component_qty', 'Qty'),
        ('component_cost', 'Cost'),
        ('updated_at', 'Updated at'),
    )
    
    def get_project(self):
        project_id = self.kwargs.get("project_id")
        print("project_id",project_id)
        # Step 1: get Project (main project)
        #projectcomponent = get_object_or_404(ProjectComponent, pk=project_id)

        # Step 2: get ProjectHeader linked to Project
        project_header = get_object_or_404(ProjectHeader, pk=project_id)
    

        project = get_object_or_404(Project, pk=project_header.project_id)

        # Step 3: budget (optional)
        budget = BudgetAllocation.objects.filter(project=project).first()
        self.MAX_COST = budget.allocated_budget if budget else 0

        return project_header

    def get_extra_context(self):
        context = super().get_extra_context()

        project = self.get_project()   # this is ProjectHeader
        total_cost = (
            ProjectComponent.objects
            .filter(project=project)
            .aggregate(total=Sum("component_cost"))
            .get("total") or 0
        )

        context.update({
            'page_title': 'Project Component',
            'model_name': 'ProjectComponent',
            'total_cost': total_cost,
            'can_add_component': total_cost < self.MAX_COST
        })

        return context
    
    def get_initial(self):
        return {
            "component_type": "BOM"  # default selection
        }
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        # Get project_id from URL or request
        project_id = (
            self.kwargs.get("project_id")
            or self.request.GET.get("project_id")
        )

        if project_id:
            kwargs["project"] = get_object_or_404(ProjectHeader, id=project_id)

        return kwargs

# ---------------- BOMHeader CRUD ----------------
class BOMHeaderCrudView(BaseCRUDView):
    model = BOMHeader
    model_url = "bom_header"
    form_class = BOMHeaderModelForm
    FieldList = (
        ('code', 'BOM Code'),
        ('project', 'Project Header'),
        ('updated_at', 'Updated at'),
    )

# ---------------- BOMItem CRUD ----------------
class BOMItemCrudView(BOMCRUDView):
    model = BOMItem
    model_url = "bom_item"     
    form_class = BOMItemModelForm
    FieldList = (
        ('code', 'BOM Item Code'),
        ('bom', 'BOM Header'),
        ('product', 'Product'),
        ('bom_quantity', 'Quantity'),
        ('bom_uom', 'UOM'),
        ('scrap_percentage', 'Scrap %'),
        ('updated_at', 'Updated at'),
    )

# ---------------- BOMAttachments CRUD View ----------------
class BOMAttachmentsCrudView(BOMCRUDView):
    model = BOMAttachments
    model_url = "bom_attachments"
    form_class = BOMAttachmentsModelForm
    FieldList = (
        ('attachment_id', 'Attachment ID'),
        ('bom', 'BOM Header'),
        ('attachment_type', 'Attachment Type'),
        ('title', 'Title'),
        ('url', 'URL'),
        ('file_name', 'File Name'),
        ('mime_type', 'MIME Type'),
        ('file_size', 'File Size (bytes)'),
        ('updated_at', 'Updated at'),
    )

    def get_extra_context(self):
        return {
            'page_title': 'BOM Attachments',
            'model_name': 'BOMAttachments',
        }

# ----------------------------
# Download view for FILE attachments
# ----------------------------

def download_attachment(request, bom_id,pk):
    attachment = get_object_or_404(BOMAttachments, pk=pk)

    if attachment.attachment_type != 'FILE' or not attachment.file_upload:
        raise Http404("File not available for download.")

    try:
        # Use FileResponse to efficiently stream the file
        return FileResponse(
            attachment.file_upload.open('rb'), 
            as_attachment=True, 
            filename=attachment.file_name
        )
    except FileNotFoundError:
        raise Http404("File not found.")


class VoucherSearchView(VoucherHeaderBaseCRUDView):
    model = VoucherHeader
    form_class = VoucherSearchModelForm

    # FieldList = (
    #              ('code','PO Code'),
    #              ('vendor__company_name1','Vendor Company Name1'),
    #              ('vendor__code','Vendor Code'),
    #              ('updated_at','Updated at'),
    #              ('search_keywords','Search Keywords')
    #              )
    
    def get_extra_context(self):
        
        return {
            
        }

def voucher_header_receipt(request, po_id):
    po_obj = get_object_or_404(VoucherHeader, id=po_id)
    
    if request.method == "POST":
        item_errors = {}
        processed = 0
        ht_items_list = []
        for item in po_obj.items.all():      

            # Collect row-specific errors
            row_errors = []  
            
            # Process valid rows
            gm_date_str = date.today().strftime("%Y-%m-%d")
            data = {
                "po_header": po_obj,
                "po_item" : item,
            }
            processed += 1
            ht_items_list.append(item.pk)

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

    return redirect(f"{reverse('voucher-search-create')}?po_id={po_id}")


def issue_voucher_edit_receipt(request, po_id):
    try:
        po_obj = get_object_or_404(VoucherHeader, id=po_id)
        if request.method == "POST":
            item_errors = {}
            processed = 0
            ht_items_list = []
            for item in po_obj.getItems():
                field_name = f"qty_being_received_{item.id}"
                qty_str = request.POST.get(field_name, "0")

                try:
                    qty_being_received = float(qty_str)
                except ValueError:
                    qty_being_received = 0

                # Collect row-specific errors
                row_errors = []

                if qty_being_received < 0:
                    row_errors.append("Quantity cannot be negative.")

                if row_errors:
                    item_errors[item.id] = row_errors
                    continue

                import pdb; pdb.set_trace();

                inv_obj = get_object_or_404(Inventory, id=item.inventory.id)
                inv_obj.quantity = int(inv_obj.quantity) - qty_being_received

                print(inv_obj.quantity, "quantity")

            # po_obj.save()
            # Save errors into session for re-render
            request.session["item_errors"] = item_errors
            request.session["last_po_id"] = po_id
            request.session['ht_items_list']=ht_items_list


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
    except Exception as e:
        print(str(e))
    
    return redirect(f"{reverse('voucher-search-create')}?po_id={po_id}")


class ProjectIssueVoucherBaseView(ProjectIssueVoucherCRUDView):
    model = VoucherHeader
    form_class = None

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
    

def issue_voucher_pdf(request, pk=None, issue_voucher_number='', report_type=''):
    
    voucher = get_object_or_404(
        GoodsMovementHeader,
        issue_voucher_number=issue_voucher_number
    )

    items = voucher.items.all()
    # for item in items:
    #     item.inventory_qty = Inventory.objects.filter(
    #         product=item.product
    #     ).aggregate(total=Sum('quantity'))['total'] or 0

    watermark_path = os.path.join(settings.BASE_DIR, 'static/default/img/priya-tr.png')

    context = {
        "voucher": voucher,
        "items": items,
        "project": voucher.project,
        "watermark_path":watermark_path
    }

    template = "project/issue_voucher_pdf.html"
    html = render_to_string(template, context)
    #html = template.render(context)

    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = f'filename="IssueVoucher_{issue_voucher_number}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse(f'We had some errors <pre>{html}</pre>')

    return response
