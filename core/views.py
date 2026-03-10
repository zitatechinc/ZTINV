# Django core imports
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.contrib import messages
from django.utils.html import format_html
from django.db.models import Q, Sum, Max, ProtectedError
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db import OperationalError

from django.utils.safestring import mark_safe
# Django authentication & decorators
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import get_object_or_404
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType

# Django generic views
from django.views import View
from django.views import generic
from django.views.generic import TemplateView
from django import forms
from django.http import HttpResponseServerError,HttpResponseNotFound
from datetime import date


# Python standard libraries
import logging
import traceback
import os
import re
import pandas as pd

# Project-specific imports
from location.models import Country
from vendor.models import Vendor, ProductVendor, VendorTax, VendorBank, VendorType
from inventory.models import PurchaseOrderHeader, PurchaseOrderItem, Inventory,RejectionCode,GoodsMovementHeader,GoodsMovementItem
from catalog.models import ProductLinks, Product, ProductType, ProductGroup, Category, Languages, Brand, Manufacturer
from project.models import ProjectHeader, BOMHeader, VoucherHeader, BOMItem, VoucherComponent, ProjectComponent
from ims.models import Project, BudgetAllocation
from accounts.forms import ChangePasswordForm
from datetime import datetime
from django.utils.timezone import make_aware

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
import traceback
import logging

logger = logging.getLogger(__name__)

# Logger setup
from django.contrib.contenttypes.models import ContentType
from auditlog.models import LogEntry
logger = logging.getLogger('console')

def custom_404(request, exception):
    return render(request, "core/404.html", status=404)

def custom_500(request):
    return render(request, "core/500.html", status=500)
    
class BaseCRUDView(PermissionRequiredMixin, LoginRequiredMixin, View):
    """Reusable base class for CRUD operations on any model."""
    model = None
    form_class = None
    raise_exception = True
    login_url = '/login/'

    paginate_by = 15
    FieldList = ()
    SORT_DICT = {
        'ASC': "",
        "DESC": "-"
    }

    action = None
    crud_method = None

    CRUD_METHODS = {
        "list": "list_view",
        "create": "create_view",
        "update": "update_view",
        "view": "read_view",
        "delete": "delete_view",
        "history": "history_view",
    }

    CRUD_PERMISSIONS = {
        "list": "view",
        "view": "view",
        "create": "create",
        "update": "edit",
        "delete": "delete",
        "history":"view",
    }

    # In BaseCRUDView (at the top)
    def get_model_url(self):
        try:
            if hasattr(self, "model_url") and self.model_url:
                return self.model_url
            # fallback to old regex if not set
            import re
            return re.sub(r'(?<!^)(?=[A-Z])', '_', self.model.__name__).lower()
        except Exception as e:
            logger.exception("Error resolving model URL")
            raise

    @property
    def CurReqPath(self):
        path = self.request.path.rstrip('/')
        return path if path else '/'

    def dispatch(self, request, pk=None, *args, **kwargs):
        """Figure out which CRUD action this is, before calling permission check."""
        self.request = request
        path_end = self.CurReqPath.lower()
        
        # Detect action
        if path_end.endswith("list"):
            self.action = "list"
        elif path_end.endswith("create"):
            self.action = "create"
        elif pk and path_end.endswith("update"):
            self.action = "update"
        elif pk and path_end.endswith("view"):
            self.action = "view"
        elif pk and path_end.endswith("delete"):
            self.action = "delete"
        elif pk and path_end.endswith("history"):  # ✅ New history action
            self.action = "history"
        else:
            return redirect("home")

        # Assign the method to call later
        self.crud_method = getattr(self, self.CRUD_METHODS[self.action])

        # Now PermissionRequiredMixin will call get_permission_required()
        return super().dispatch(request, pk=pk, *args, **kwargs)

    def get_permission_required(self):
        """Return permission string based on action + model."""
        
        if not self.model:
            return []

        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        perm_type = self.CRUD_PERMISSIONS.get(self.action, "view")
        if model_name == "logentry":
            return []
        else:
            perm = f"{app_label}.can_{perm_type}_{model_name}"
            print("Checking permission:", perm)
            return [perm]

    def handle_no_permission(self):
        """Custom response when user lacks permission."""
        if not self.request.user.is_authenticated:
            # still respect login redirect
            return super().handle_no_permission()

        # Show a friendly page
        return HttpResponseForbidden(
            render(self.request, "core/403.html", {
                "message": "It looks like you don’t have permission to view this content"
            })
        )

    def handle_not_found(self, message=None):
        """Custom response for 404 Not Found."""
        return HttpResponseNotFound(
            render(self.request, "core/404.html", {
                "message": message or "The page you’re looking for doesn’t exist."
            })
        )
    
    def handle_server_error(self, message=None):
        """Custom response for 500 Server Error."""
        return HttpResponseServerError(
            render(self.request, "core/500.html", {
                "message": message or "Something went wrong on our end. Please try again later."
            })
        )

    def get(self, request, pk=None, *args, **kwargs):
        return self.crud_method(pk) if pk else self.crud_method()

    def post(self, request, pk=None, *args, **kwargs):
        return self.crud_method(pk) if pk else self.crud_method()

    @property
    def PageNumber(self):
        try:
            return int(self.request.GET.get('page', 1))
        except (TypeError, ValueError):
            return 1

    @property
    def QuerySearch(self):
        return self.request.GET.get('QuerySearch', '')

    @property
    def FieldName(self):
        return self.request.GET.get('FieldName', '').strip()

    @property
    def RecordStatus(self):
        return self.request.GET.get('RecordStatus', '').strip()

    @property
    def Keyword(self):
        return self.request.GET.get('Keyword', '').strip()

    @property
    def OrderByColumn(self):
        if self.request.GET.get('OrderByColumn'):
            val =  self.request.GET.get('OrderByColumn', 'id')
        else:
            val = 'id'
        return val        

    @property
    def SortByColumn(self):
        if self.request.GET.get('SortByColumn', 'DESC'):
            return self.request.GET.get('SortByColumn', 'DESC').strip()
        else:
            return 'DESC'
        
    @property
    def getOrderandSortbyColumn(self):
        return self.SORT_DICT[self.SortByColumn] + self.OrderByColumn

    @property
    def ListName(self):
        return f"{self.model._meta.verbose_name.title()}"

    @property
    def FormName(self):
        return f"{self.model._meta.verbose_name.title()} Form"

    @property
    def ViewName(self):
        return f"{self.model._meta.verbose_name.title()} View"
    
    def getTableConfig(self):
        return {
            "SortByColumn" : self.SortByColumn,
            "OrderByColumn" : self.OrderByColumn,
            "Keyword" : self.Keyword,
            "FieldName" : self.FieldName,
            "RecordStatus": self.RecordStatus,
            "FieldList": self.FieldList,
            "PageSizeOptions": [10, 25, 50, 100],
        }

    def get_extra_context(self):
        return {}

    # def get_success_url(self, op):
    #     app_label = self.model._meta.app_label
    #     model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self.model.__name__).lower()
    #     return f'/{app_label}/{model_name}/{op}'

    # def get_form_action_url(self, op):
    #     app_label = self.model._meta.app_label
    #     model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self.model.__name__).lower()
    #     return f'/{app_label}/{model_name}/{op}'

    def get_success_url(self, op):
        app_label = self.model._meta.app_label
        model_name = self.get_model_url()
        return f'/{app_label}/{model_name}/{op}'

    def get_form_action_url(self, op):
        app_label = self.model._meta.app_label
        model_name = self.get_model_url()
        return f'/{app_label}/{model_name}/{op}'
    
    def get_tabform_action_url(self, op,obj=None):
        app_label = self.model._meta.app_label
        model_name = self.get_model_url()
        if 'bom' in model_name:
            model_name = model_name.replace('bom','b_o_m')
        print(f'/{app_label}/{model_name}/{op}')
        return f'/{app_label}/{obj.pk}/{model_name}/{op}'

    def get_vendor_form_action_url(self,  vendor_id, op):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self.model.__name__).lower()
        return f'/{app_label}/{vendor_id}/{model_name}/{op}'
    
    def get_productvendor_form_action_url(self,  product_id, op):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self.model.__name__).lower()
        return f'/{app_label}/{product_id}/{model_name}/{op}'
    
    def get_vendorproduct_form_action_url(self,  vendor_id, op):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self.model.__name__).lower()
        return f'/{app_label}/{vendor_id}/vendor_product/{op}'

    def getTemplateName(self, op, suffixes='.html'):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self.model.__name__).lower()
        print(f'{app_label}/{model_name}_{op}{suffixes}')
        return f'{app_label}/{model_name}_{op}{suffixes}'
    
    def getGoodsTemplateName(self, op, suffixes='.html'):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self.model.__name__).lower()
        return f'{app_label}/goods_receiver_{op}{suffixes}'

    def getQMTemplateName(self, op, suffixes='.html'):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self.model.__name__).lower()
        return f'{app_label}/quality_management_{op}{suffixes}'

    def getPOReportemplateName(self, op, suffixes='.html'):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self.model.__name__).lower()
        return f'{app_label}/po_report_{op}{suffixes}'

    def getProjectTemplateName(self, op, suffixes='.html'):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self.model.__name__).lower()
        return f'{app_label}/project_{op}{suffixes}'

    def getVoucherTemplateName(self, op, suffixes='.html'):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self.model.__name__).lower()
        return f'{app_label}/voucher_{op}{suffixes}'    

    def getBomTemplateName(self, op, suffixes='.html'):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self.model.__name__).lower()
        return f'{app_label}/bom_{op}{suffixes}'

    def getInventorySearchTemplateName(self, op, suffixes='.html'):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self.model.__name__).lower()
       
        return f'{app_label}/inventory_search_{op}{suffixes}'

    def getVendorProductTemplateName(self, op, suffixes='.html'):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self.model.__name__).lower()
        return f'{app_label}/vendor_product_{op}{suffixes}'          

    def getListBreadCrumList(self):
        return [
            {"url" : '/', "name" : "Home", 'status' : ''}, 
            {"url" : '', "name" : self.ListName, "status" : "active"}]
    
    def getBomListBreadCrumList(self,obj,item):
        app_label = obj._meta.app_label
        #model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', item._meta.model_name ).lower()
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', item._meta.model.__name__).lower()
        #item_lable =item._meta.app_label
        print("app_label",app_label)
        data =[
            {"url" : '/', "name" : "Home", 'status' : ''}, 
            {"url" : f'/{app_label}/{obj.pk}/{model_name}/list', "name" : self.ListName, "status" : "active"}]
        # if item:
        #     data.append({"url" : '#', "name" :self.get_form_action_url('view'), "status" : "active"},)
        if item:
            data.append({"url" : '#', "name" : self.ViewName + f"<small> ({item.get_name}) </small>",  "status" : "active"})
        else:
            data.append({"url" : '#', "name" : self.ViewName,  "status" : "active"})

        return data
    
    def getAuditListBreadCrumList(self):
        return [
            {"url" : '/', "name" : "Home", 'status' : ''}, 
            {"url" : self.get_form_action_url('list'), "name" : self.ListName, "status" : "active"}]

    def getVendorListBreadCrumList(self, vendor_obj, po_obj=None):
        data = [
            {"url" : '/', "name" : "Home", 'status' : ''}, 
            {"url" : f'/vendor/vendor/{vendor_obj.pk}/view', "name" : f"Vendor Details ({vendor_obj.company_name1})", "status" : ""}
            ]
        if po_obj:
            data.append(
                {"url" : f'/vendor/{vendor_obj.pk}/purchase_order_header/{po_obj.pk}/view', "name" : f"Purchase Order Details ({po_obj.code})", "status" : ""}
                )
        data.append({"url" : '#', "name" : self.ListName, "status" : "active"})
        return data
    
    def getProductVendorListBreadCrumList(self, product_obj):
        return [
            {"url" : '/', "name" : "Home", 'status' : ''}, 
            {"url" : f'/catalog/product/{product_obj.pk}/view', "name" : f"Product Details ({product_obj.name})", "status" : ""},
            {"url" : '#', "name" : self.ListName, "status" : "active"},
            ]            

    def getFormBreadCrumList(self, obj=None):
        data = [
            {"url" : '/', "name" : "Home", 'status' : ''}, 
            {"url" : self.get_form_action_url('list'), "name" : self.ListName, "status" : ""},
            ]
        if obj:
            data.append({"url" : '#', "name" : self.FormName + f"<small> ({obj.get_name}) </small>",  "status" : "active"})
        else:
            data.append({"url" : '#', "name" : self.FormName ,  "status" : "active"})
        return data

    def camel_to_snake(self,name):
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
    
    def get_tablist_action_url(self,op,obj=None):
        app_label = self.model._meta.app_label
        model_name = self.get_model_url()
        if 'bom' in model_name:
            model_name = model_name.replace('bom','b_o_m')
        print(f'/{app_label}/{model_name}/{op}')
        return f'/{app_label}/{self.camel_to_snake(obj.__class__.__name__)}/{obj.pk}/{op}' 

    def getProjectBreadCrumList(self,header_obj=None,item_obj=None):
        data = [
            {"url" : '/', "name" : "Home", 'status' : ''}, 
            {"url" : self.get_tablist_action_url('view',header_obj), "name" : header_obj.__class__.__name__, "status" : ""},
            ]
        return data
    
    def getProjectItemBreadCrumList(self,header_obj=None,obj=None):
        data = [
            {"url" : '/', "name" : "Home", 'status' : ''}, 
            {"url" : f'/project/{header_obj.pk}/project_component/list', "name" : obj.__class__.__name__, "status" : ""},
            ]
        if obj:
            data.append({"url" : '#', "name" : self.FormName + f"<small> ({obj.get_name}) </small>",  "status" : "active"})
        else:
            data.append({"url" : '#', "name" : self.FormName ,  "status" : "active"})
        return data

    def getTabFormBreadCrumList(self, obj=None):
        data = [
            {"url" : '/', "name" : "Home", 'status' : ''}, 
            {"url" : self.get_tabform_action_url('list',obj), "name" : self.ListName, "status" : ""},
            ]
        if obj:
            data.append({"url" : '#', "name" : self.FormName + f"<small> ({obj.get_name}) </small>",  "status" : "active"})
        else:
            data.append({"url" : '#', "name" : self.FormName ,  "status" : "active"})
        return data

    def getReadBreadCrumList(self, obj=None):
        data = [
            {"url" : '/', "name" : "Home", 'status' : ''}, 
            {"url" : self.get_form_action_url('list'), "name" : self.ListName, "status" : ""},
            ]
        if obj:
            data.append({"url" : '#', "name" : self.ViewName + f"<small> ({obj.get_name}) </small>",  "status" : "active"})
        else:
            data.append({"url" : '#', "name" : self.ViewName,  "status" : "active"})
        
        return data

    def globalSearchQuerySet(self, **kwargs):
        try:
            if self.Keyword:
                query_conditions = Q()
                for field in self.model.get_search_fields():
                    query_conditions |= Q(**{f"{field}__icontains": self.Keyword})
                queryset = self.model.objects.filter(query_conditions)
                if kwargs:
                    queryset = queryset.filter(**kwargs)
            else:
                queryset = self.model.objects.filter(**kwargs)
        except Exception as e:
            queryset = self.model.objects.none()
            print (e)
        
        return queryset

    # def getListQuerySet(self, **kwargs):
    #     try:
    #         filter_kwargs = {}
    #         if self.RecordStatus:
    #             filter_kwargs.update({self.model.get_status_col_name() : self.RecordStatus})
    #         if self.Keyword and self.FieldName:
    #             filter_kwargs.update({f"{self.FieldName}__icontains": self.Keyword})
    #             filter_kwargs.update(kwargs)
    #             queryset = self.model.objects.filter(**filter_kwargs)
    #         else:
    #             if self.RecordStatus:
    #                 kwargs[self.model.get_status_col_name()] = self.RecordStatus
    #             queryset = self.globalSearchQuerySet(**kwargs)

    #         if self.getOrderandSortbyColumn and queryset:
    #             queryset = queryset.order_by(self.getOrderandSortbyColumn)
    #     except Exception as e:
    #         print (e)
    #         queryset = self.model.objects.all()
    #     return queryset

    def getListQuerySet(self, **kwargs):
        """
        Returns queryset with records ordered by:
        1. Status: Active (1) -> Draft (0) -> Inactive (-1)
        2. Then by existing sort column if provided
        """
        try:
            filter_kwargs = {}
            status_col = self.model.get_status_col_name()  # your status field
            # Apply record status filter if provided
            if self.RecordStatus:
                filter_kwargs.update({self.model.get_status_col_name() : self.RecordStatus})

            # Apply keyword search
            if self.Keyword and self.FieldName:
                filter_kwargs.update({f"{self.FieldName}__icontains": self.Keyword})
                filter_kwargs.update(kwargs)
                queryset = self.model.objects.filter(**filter_kwargs)
            else:
                if self.RecordStatus:
                    kwargs[status_col] = self.RecordStatus
                queryset = self.globalSearchQuerySet(**kwargs)

            # --- Custom ordering by numeric status ---
            from django.db.models import Case, When, IntegerField

            status_order = [1, 0, -1]  # Active -> Draft -> Inactive
            order_cases = [When(**{status_col: s}, then=i) for i, s in enumerate(status_order)]

            queryset = queryset.annotate(
                status_ordering=Case(
                    *order_cases,
                    default=99,
                    output_field=IntegerField()
                )
            )

            # Apply existing sorting if specified
            if self.getOrderandSortbyColumn:
                queryset = queryset.order_by('status_ordering', self.getOrderandSortbyColumn)
            else:
                queryset = queryset.order_by('status_ordering')

        except Exception as e:
            print("Error in getListQuerySet:", e)
            queryset = self.model.objects.all()

        return queryset
    
    def _build_audit_logs(self, request, queryset):
        keyword = request.GET.get("Keyword", "").strip().lower()
        field = request.GET.get("FieldName")

        logs = []

        paginator = Paginator(queryset, 10)
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        for entry in page_obj:
            for column, (old, new) in (entry.changes_dict or {}).items():

                if keyword:
                    if field == "column" and keyword not in column.lower():
                        continue
                    if field == "value" and not (
                        keyword in str(old).lower() or
                        keyword in str(new).lower()
                    ):
                        continue

                logs.append({
                    "EntityName": entry.content_type.model,
                    "RowID": entry.object_id,
                    "ColumnName": column,
                    "OldValue": old,
                    "NewValue": new,
                    "Action": entry.get_action_display(),
                    "User": entry.actor.username if entry.actor else None,
                    "Timestamp": entry.timestamp,
                })

        return logs, page_obj
    
    def get_audit_fields(self):
        return (
            ("column", "Column"),
            ("value", "Old / New Value"),
        )
    
    def history_view(self, pk):
        obj = self.model.objects.get(pk=pk)
        request = self.request

        ct = ContentType.objects.get_for_model(obj)

        queryset = LogEntry.objects.filter(
            content_type=ct,
            object_id=str(obj.pk)
        ).select_related(
            "actor", "content_type"
        ).order_by("-timestamp")

        # reuse common audit search logic
        logs, page_obj = self._build_audit_logs(request, queryset)
        print()

        context = {
            "object": obj,
            "object_list": logs,
            "page_obj": page_obj,
            "FieldList": self.get_audit_fields(),
            "FieldName": request.GET.get("FieldName"),
            "Keyword": request.GET.get("Keyword",''),
             "BreadCrumList" : self.getAuditListBreadCrumList(),
            "active_tab": "history",
        }

        #return render(request, self.audit_template_name, context)
        #context.update(self.getTableConfig())
        context.update(self.get_extra_context())
        return render(self.request, self.getTemplateName('history'), context)

    def list_view(self):
        logger.info("Entered BaseCRUDView->list_view")
        try:
            self.request = self.request
            queryset = self.getListQuerySet()
            TotalRecords = queryset.count()
            logger.debug(f"Total records fetched: {TotalRecords}")

            page_size = self.request.GET.get("page_size", self.paginate_by)
            page_size = int(page_size)
            if TotalRecords > 0:
                paginator = Paginator(queryset, page_size)
                page_obj = paginator.get_page(self.PageNumber)
            else:
                paginator = Paginator([], self.paginate_by)
                page_obj = paginator.get_page(0)

            logger.info("Pagination completed successfully")
            context = {
                'object_list': page_obj,
                'page_obj': page_obj,
                'paginator': paginator,
                'is_paginated': page_obj.has_other_pages(),
                "model_name" : self.model._meta.verbose_name,
                "RecordsTotal" : TotalRecords,
                "PageNumber" : self.PageNumber,
                'page_title': self.ListName,
                 "PageSize": page_size,
                "BreadCrumList" : self.getListBreadCrumList(),
               
                "CancelURL" : '/'
            }
            context.update(self.getTableConfig())
            context.update(self.get_extra_context())

            logger.info("Rendering BaseCRUDView->list view template")
            return render(self.request, self.getTemplateName('list'), context)
        except Exception as e:
            logger.error(
                f"Exception in BaseCRUDView->list_view | Path: {self.request.path}",
                exc_info=True
            )
            # traceback.print_exc()
            # logger.debug(f"BaseCRUDView->list_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info) 
        
    def create_view(self):
        #logger.info("Entered BaseCRUDView->create_view")
        logger.info(f"Entered BaseCRUDView->create_view | Model: {self.model.__name__}")
        try:
            if self.request.method == 'POST':
                logger.info("POST request received in BaseCRUDView->create_view")
                form = self.form_class(self.request.POST, self.request.FILES)

                if form.is_valid():
                    logger.debug("Form validation successful")
                    obj = form.save(commit=False)

                    # Remove image if requested
                    if form.cleaned_data.get('remove_image'):
                        logger.debug("Image removal requested")
                        if obj.image:
                            obj.image.delete(save=False)
                        obj.image = None

                    # Set created_user if exists
                    if hasattr(obj, 'created_user'):
                        obj.created_user = self.request.user

                    obj.save()
                    logger.info(f"{self.model.__name__} created successfully with ID {obj.pk}")
                    messages.success(self.request, f"{self.model._meta.verbose_name} record created successfully.")
                    return redirect(self.get_success_url('list'))
                
                else:
                    # Append all field errors into one message
                    logger.warning("Form validation failed")
                    logger.debug(form.errors)
                    error_messages = []
                    for field, errors in form.errors.items():
                        for error in errors:
                            field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                            error_messages.append(f"<li><strong style='font-size: 14px !important; font-weight: bold !important'>{field_label}:</strong> {error}</li>")
                    full_error_message = "<ul>" + "".join(error_messages) + "</ul>"

                    messages.error(self.request,mark_safe(full_error_message))

            else:
                logger.info("GET request received in BaseCRUDView->create_view")
                form = self.form_class()

            context = {
                'form': form,
                "form_action_url": self.get_form_action_url('create'),
                "model_name": self.model._meta.verbose_name,
                'page_title': self.FormName,
                "BreadCrumList": self.getFormBreadCrumList(),
                "CancelURL": '/',
            }
            context.update(self.get_extra_context())
            context.update(self.getTableConfig())
            logger.info("Rendering create form")
            return render(self.request, self.getTemplateName('form'), context)

        except Exception as e:
            # traceback.print_exc()
            # logger.debug(f"BaseCRUDView->create_view: {self.request.path}, Exception: {e}")
            logger.error(
                f"Exception in BaseCRUDView->create_view | Path: {self.request.path}",
                exc_info=True
            )
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    def update_view(self, pk):
        logger.info(f"Entered BaseCRUDView->update_view | Model: {self.model.__name__} | ID: {pk}")
        try:
            obj = get_object_or_404(self.model, pk=pk)
            if self.request.method == 'POST':
                logger.info("POST request received in BaseCRUDView->update_view")
                form = self.form_class(self.request.POST, self.request.FILES, instance=obj)

                if form.is_valid():
                    obj = form.save(commit=False)
                    logger.info(f"{self.model.__name__} updated successfully | ID: {pk}")
                    obj.save()

                    # User model group handling
                    if self.model.__name__ == 'User':
                        if isinstance(obj, self.model):
                            obj.groups.clear()
                            role = form.cleaned_data.get("groups")
                            if role:
                                obj.groups.add(role)

                    messages.success(self.request, f"{self.model._meta.verbose_name} record updated successfully.")
                    form = self.form_class(instance=obj)
                
                else:
                    # Append all field errors into one message
                    logger.warning("Form validation failed in BaseCRUDView->update_view")
                    logger.debug(form.errors)
                    error_messages = []

                    for field, errors in form.errors.items():
                        for error in errors:
                            field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                            error_messages.append(f"<li><strong style='font-size: 14px !important; font-weight: bold !important'>{field_label}:</strong> {error}</li>")
                    full_error_message = "<ul>" + "".join(error_messages) + "</ul>"

                    messages.error(self.request,mark_safe(full_error_message))

            else:
                logger.info("GET request received in BaseCRUDView->update_view")
                form = self.form_class(instance=obj)

            context = {
                'form': form,
                'object': obj,
                "form_action_url": self.get_form_action_url(f'{pk}/update'),
                "model_name": self.model._meta.verbose_name,
                'page_title': self.FormName,
                "CancelURL": '/',
                "BreadCrumList": self.getFormBreadCrumList(obj),
            }
            context.update(self.get_extra_context())
            context.update(**self.getTableConfig())
            logger.info("Rendering update form")
            return render(self.request, self.getTemplateName('form'), context)

        except Exception as e:
            logger.error(
                f"Exception in BaseCRUDView->update_view | ID: {pk} | Path: {self.request.path}",
                exc_info=True
            )
            # traceback.print_exc()
            # logger.debug(f"BaseCRUDView->update_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)
    
    def read_view(self, pk):
        logger.info(f"Entered BaseCRUDView->read_view | Model: {self.model.__name__} | ID: {pk}")
        try:
            logger.debug("Fetching object from database")
            obj = get_object_or_404(self.model, pk=pk)
            logger.debug("Initializing form in read-only mode")

            form = self.form_class(instance=obj)
            context = {"form_action_url" :  self.get_form_action_url(f'{pk}/update'),
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.ViewName,
            "BreadCrumList" : self.getReadBreadCrumList(obj),
            "CancelURL" : '/',
            'object' : obj,
            'form' : form
            }
            logger.debug("Updating context with extra and table configuration")
            context.update(self.get_extra_context())
            context.update(self.getTableConfig())

            logger.info("Rendering BaseCRUDView->read/view template")
            return render(self.request, self.getTemplateName('view'), context)
        except Exception as e:
            logger.error(
                f"Unhandled exception in BaseCRUDView->read_view | Path: {self.request.path} | ID: {pk}",
                exc_info=True
            )
            # traceback.print_exc()
            # logger.debug(f"BaseCRUDView->read_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    def delete_view(self, pk):
        logger.info(f"Entered BaseCRUDView->delete_view | Model: {self.model.__name__} | ID: {pk}")
        try:
            redirect_to = self.request.GET.get('next')
            if not redirect_to:
                logger.warning("Delete attempted without redirect URL")
                messages.error(self.request, "Invalid Action.")
                return redirect(self.request.path_info)

            try:
                obj = get_object_or_404(self.model, pk=pk)

                # Handle User separately
                if self.model._meta.verbose_name.lower() == 'user':
                    obj.is_active = False
                    action_desc = "deactivated"
                else:
                    obj.status = -1
                    action_desc = "status changed"

                obj.save()
                messages.success(
                    self.request,
                    f"{obj.get_name} ({obj._meta.verbose_name.title()}) record {action_desc} successfully."
                )

            except ProtectedError:
                messages.error(
                    self.request,
                    f"This {obj.get_name} ({obj._meta.verbose_name}) record cannot be deleted because it is linked to existing records."
                )
            except ValidationError as ve:
                # Optional: if your model raises ValidationError
                error_messages = []
                for field, errors in ve.message_dict.items():
                    field_label = getattr(obj._meta.get_field(field), 'verbose_name', field).title()
                    for error in errors:
                        error_messages.append(f"<li><strong>{field_label}:</strong> {error}</li>")
                full_error_message = "<ul>" + "".join(error_messages) + "</ul>"
                messages.error(self.request, mark_safe(full_error_message))
            except Exception as e:
                messages.error(self.request, f"Something went wrong: {e}. Please try again later.")

            return redirect(redirect_to)

        except Exception as e:
            logger.error(
                f"Exception in BaseCRUDView-> delete_view | ID: {pk} | Path: {self.request.path}",
                exc_info=True
            )
            # traceback.print_exc()
            # logger.debug(f"BaseCRUDView->delete_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    #History View
    # def history_view(self,pk):
    #     exclude_fields = ['updated_at','slug']
    #     try:
    #         obj = get_object_or_404(self.model, pk=pk)
    #         history_list = obj.history.all().order_by('-history_date')
    #         print("history_list:",history_list)
    #         history_data = []
    #         for i, record in enumerate(history_list):
    #             changes = {}
    #             if i + 1 < len(history_list):  # Compare with previous version
    #                 previous = history_list[i + 1]
    #                 for field in self.model._meta.fields:
    #                     if field.name not in exclude_fields:

    #                         field_name = field.name
    #                         old_value = getattr(previous, field_name)
    #                         new_value = getattr(record, field_name)

    #                         if old_value != new_value:
    #                             # field changed → highlight with +
    #                             changes[field.verbose_name] = format_html(
    #                                 "<span style='color:green;'>+ {}</span> → <span style='color:red;'>- {}</span>",
    #                                 new_value, old_value
    #                             )
    #             else:
    #                 # First record (no previous one)
    #                 for field in self.model._meta.fields:
    #                     changes[field.verbose_name] = format_html(
    #                         "<span style='color:gray;'>Initial: {}</span>", getattr(record, field.name)
    #                     )

    #             history_data.append({
    #                 "history_date": record.history_date,
    #                 "history_user": record.history_user,
    #                 "changes": changes,
    #             })
    #         context = {
    #             "obj": obj,
    #             "history_list": history_data,
    #             "CancelURL" : '/',
    #             "page_title": f"{self.model._meta.verbose_name} History",
    #         }
    #         return render(self.request, self.getTemplateName('history'), context)
    #     except Exception as e:
    #         traceback.print_exc()
    #         pass


class AccountCRUDView(LoginRequiredMixin, View):
    """
    Reusable base class for CRUD operations on any model.
    """

    model = None
    form_class = None
    raise_exception = True
    login_url = '/login/'

    paginate_by = 10
    FieldList = ()
    SORT_DICT = {
        'ASC': "",
        "DESC": "-"
    }

    action = None
    crud_method = None

    CRUD_METHODS = {
        "list": "list_view",
        "create": "create_view",
        "update": "update_view",
        "view": "read_view",
        "delete": "delete_view",
        "changepassword": "change_password_view",
    }

    CRUD_PERMISSIONS = {
        "list": "view",
        "view": "view",
        "create": "create",
        "update": "edit",
        "delete": "delete",
    }

    @property
    def CurReqPath(self):
        path = self.request.path.rstrip('/')
        return path if path else '/'

    # def dispatch(self, request, pk=None, *args, **kwargs):
    #     """Figure out which CRUD action this is, before calling permission check."""
    #     self.request = request
    #     path_end = self.CurReqPath.lower()

    #     # Detect action
    #     if path_end.endswith("list"):
    #         self.action = "list"
    #     elif path_end.endswith("create"):
    #         self.action = "create"
    #     elif pk and path_end.endswith("update"):
    #         self.action = "update"
    #     elif pk and path_end.endswith("view"):
    #         self.action = "view"
    #     elif pk and path_end.endswith("delete"):
    #         self.action = "delete"
    #     else:
    #         return redirect("home")

    #     # Assign the method to call later
    #     self.crud_method = getattr(self, self.CRUD_METHODS[self.action])

    #     # Now PermissionRequiredMixin will call get_permission_required()
    #     return super().dispatch(request, pk=pk, *args, **kwargs)

    def dispatch(self, request, pk=None, *args, **kwargs):
        """Determine action type and enforce role-based access."""
        self.request = request
        path_end = self.CurReqPath.lower()

        # Detect CRUD action
        if path_end.endswith("list"):
            self.action = "list"
        elif path_end.endswith("create"):
            self.action = "create"
        elif pk and path_end.endswith("update"):
            self.action = "update"
        elif pk and path_end.endswith("view"):
            self.action = "view"
        elif pk and path_end.endswith("delete"):
            self.action = "delete"
        elif pk and path_end.endswith("changepassword"):
            self.action = "changepassword"
        else:
            return redirect("home")

        # Role-based access mapping
        ROLE_PERMISSIONS = {
            "Administrator": ["list", "create", "update", "delete", "view","changepassword"],
            "Staff": ["list", "create", "view","changepassword"],
            "Guest": ["list", "view","changepassword"],
        }

        # Detect user role (either from user.role or first group name)
        user_role = getattr(request.user, "role", None)
        if not user_role and request.user.groups.exists():
            user_role = request.user.groups.first().name
        if not user_role:
            user_role = "Guest"  # fallback
        print("self.action",self.action )
        # Enforce role restriction
        if self.action not in ROLE_PERMISSIONS.get(user_role, []):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied(f"Role '{user_role}' not allowed to perform '{self.action}' action.")

        # Assign method to call later
        self.crud_method = getattr(self, self.CRUD_METHODS[self.action])

        # Call super dispatch (PermissionRequiredMixin runs next)
        return super().dispatch(request, pk=pk, *args, **kwargs)


    def get_permission_required(self):
        """Return permission string based on action + model."""
        if not self.model:
            return []

        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        perm_type = self.CRUD_PERMISSIONS.get(self.action, "view")

        # Full permission codename with app label
        perm = f"{app_label}.can_{perm_type}_{model_name}"
        print("Checking permission:", perm)  # DEBUG
        return [perm]

    def handle_no_permission(self):
        """Custom response when user lacks permission."""
        print("handle_no_permissionhandle_no_permission")
        if not self.request.user.is_authenticated:
            # still respect login redirect
            return super().handle_no_permission()

        # Show a friendly page
        return HttpResponseForbidden(
            render(self.request, "core/403.html", {
                "message": "It looks like you don’t have permission to view this content"
            })
        )

    def get(self, request, pk=None, *args, **kwargs):
        return self.crud_method(pk) if pk else self.crud_method()

    def post(self, request, pk=None, *args, **kwargs):
        return self.crud_method(pk) if pk else self.crud_method()

    @property
    def PageNumber(self):
        try:
            return int(self.request.GET.get('page', 1))
        except (TypeError, ValueError):
            return 1

    @property
    def QuerySearch(self):
        return self.request.GET.get('QuerySearch', '')

    @property
    def FieldName(self):
        return self.request.GET.get('FieldName', '').strip()

    @property
    def RecordStatus(self):
        return self.request.GET.get('RecordStatus', '').strip()

    @property
    def Keyword(self):
        return self.request.GET.get('Keyword', '').strip()

    @property
    def OrderByColumn(self):
        if self.request.GET.get('OrderByColumn'):
            val =  self.request.GET.get('OrderByColumn', 'id')
        else:
            val = 'id'
        return val        

    @property
    def SortByColumn(self):
        if self.request.GET.get('SortByColumn', 'DESC'):
            return self.request.GET.get('SortByColumn', 'DESC').strip()
        else:
            return 'DESC'
    @property
    def getOrderandSortbyColumn(self):
        return self.SORT_DICT[self.SortByColumn] + self.OrderByColumn

    @property
    def ListName(self):
        return f"{self.model._meta.verbose_name.title()}"

    @property
    def FormName(self):
        return f"{self.model._meta.verbose_name.title()} Form"

    @property
    def ViewName(self):
        return f"{self.model._meta.verbose_name.title()} View"
    
    
    def getTableConfig(self):
        return {
            "SortByColumn" : self.SortByColumn,
            "OrderByColumn" : self.OrderByColumn,
            "Keyword" : self.Keyword,
            "FieldName" : self.FieldName,
            "RecordStatus": self.RecordStatus,
            "FieldList": self.FieldList,
             "PageSizeOptions": [10, 25, 50, 100],
            
        }

    def get_extra_context(self):
        return {}

    def get_success_url(self, op):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self.model.__name__).lower()
        return f'/{app_label}/{model_name}/{op}'

    def get_form_action_url(self, op):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self.model.__name__).lower()
        return f'/{app_label}/{model_name}/{op}'

    def get_vendor_form_action_url(self,  vendor_id, op):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self.model.__name__).lower()
        return f'/{app_label}/{vendor_id}/{model_name}/{op}'
    
    def get_productvendor_form_action_url(self,  product_id, op):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self.model.__name__).lower()
        return f'/{app_label}/{product_id}/{model_name}/{op}'

    def getTemplateName(self, op, suffixes='.html'):
        app_label = self.model._meta.app_label
        model_name = re.sub(r'(?<!^)(?=[A-Z])', '_', self.model.__name__).lower()
        return f'{app_label}/{model_name}_{op}{suffixes}'

    def getListBreadCrumList(self):
        return [
            {"url" : '/', "name" : "Home", 'status' : ''}, 
            {"url" : '#', "name" : self.ListName, "status" : "active"}]

    def getProductVendorListBreadCrumList(self, product_obj):
        return [
            {"url" : '/', "name" : "Home", 'status' : ''}, 
            {"url" : f'/catalog/product/{product_obj.pk}/view', "name" : f"Product Details ({product_obj.name})", "status" : ""},
            {"url" : '#', "name" : self.ListName, "status" : "active"},
            ]            

    def getFormBreadCrumList(self, obj=None):
        data = [
            {"url" : '/', "name" : "Home", 'status' : ''}, 
            {"url" : self.get_form_action_url('list'), "name" : self.ListName, "status" : ""},
            
            ]
        if obj:
            data.append({"url" : '#', "name" : self.FormName + f"<small> ({obj.get_name}) </small>",  "status" : "active"})
        else:
            data.append({"url" : '#', "name" : self.FormName ,  "status" : "active"})
        return data

    def getReadBreadCrumList(self, obj=None):
        data = [
            {"url" : '/', "name" : "Home", 'status' : ''}, 
            {"url" : self.get_form_action_url('list'), "name" : self.ListName, "status" : ""},
            
            ]
        if obj:
            data.append({"url" : '#', "name" : self.ViewName + f"<small> ({obj.get_name}) </small>",  "status" : "active"})
        else:
            data.append({"url" : '#', "name" : self.ViewName,  "status" : "active"})
        
        return data

    def globalSearchQuerySet(self, **kwargs):
        try:
            if self.Keyword:
                query_conditions = Q()
                for field in self.model.get_search_fields():
                    query_conditions |= Q(**{f"{field}__icontains": self.Keyword})
                queryset = self.model.objects.filter(query_conditions)
                if kwargs:
                    queryset = queryset.filter(**kwargs)
            else:
                queryset = self.model.objects.filter(**kwargs)
        except Exception as e:
            queryset = self.model.objects.none()
            print (e)
        
        return queryset

    def getListQuerySet(self, **kwargs):
        try:
            filter_kwargs = {}
            if self.RecordStatus:
                filter_kwargs.update({self.model.get_status_col_name() : self.RecordStatus})
            
            if self.Keyword and self.FieldName:
                filter_kwargs.update({f"{self.FieldName}__icontains": self.Keyword})
                filter_kwargs.update(kwargs)
                queryset = self.model.objects.filter(**filter_kwargs)
            else:
                if self.RecordStatus:
                    kwargs[self.model.get_status_col_name()] = self.RecordStatus
                queryset = self.globalSearchQuerySet(**kwargs)

            if self.getOrderandSortbyColumn and queryset:
                queryset = queryset.order_by(self.getOrderandSortbyColumn)
        except Exception as e:
            print (e)
            queryset = self.model.objects.all()
        return queryset


    def list_view(self):
        try:
            self.request = self.request
            queryset = self.getListQuerySet()
            TotalRecords = queryset.count()
            page_size = self.request.GET.get("page_size", self.paginate_by)
            page_size = int(page_size)
            if TotalRecords > 0:
                paginator = Paginator(queryset, page_size)
                page_obj = paginator.get_page(self.PageNumber)
            else:
                paginator = Paginator([], self.paginate_by)
                page_obj = paginator.get_page(0)


            context = {
                'object_list': page_obj,
                'page_obj': page_obj,
                'paginator': paginator,
                'is_paginated': paginator.num_pages > 1,
                "model_name" : self.model._meta.verbose_name,
                "RecordsTotal" : TotalRecords,
                "PageNumber" : self.PageNumber,
                'page_title': self.ListName,
                "BreadCrumList" : self.getListBreadCrumList(),
                "page_size":page_size,
                "CancelURL" : '/'
            }
            context.update(self.getTableConfig())
            context.update(self.get_extra_context())
            return render(self.request, self.getTemplateName('list'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"BaseCRUDView->list_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info) 
        
    # Create view
    def create_view(self):
        try:
            if self.request.method == 'POST':
                form = self.form_class(self.request.POST, self.request.FILES)

                if form.is_valid():
                    obj = form.save(commit=False)
                    # remove image
                    if form.cleaned_data.get('remove_image'):
                        obj.image.delete(save=False)
                        obj.image=None
                        obj.save()
                    if hasattr(obj, 'created_user'):
                        obj.created_user=self.request.user

                    obj.set_password('meslova@123')
                    obj.save()
                    obj.groups.clear()
                    role = form.cleaned_data.get("groups")
                    if role:
                        obj.groups.set([role])

                        # ✅ Superuser Logic
                        if role.name == "Administrator":
                            obj.is_superuser = True
                            obj.is_staff = True
                        else:
                            obj.is_superuser = False
                            obj.is_staff = False

                        obj.save()
                    
                    messages.success(self.request, f"{self.model._meta.verbose_name} record created successfully.")
                    return redirect(self.get_success_url('list'))
                else:
                    # error_fields = ', '.join(form.errors.keys())
                    # messages.error(self.request, f"Fields {error_fields} are missing or incorrect. Please review the form and try again.")
                    # # Append all field errors into one message
                    error_messages = []
                    for field, errors in form.errors.items():
                        for error in errors:
                            field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                            error_messages.append(f"<li><strong style='font-size: 14px !important; font-weight: bold !important'>{field_label}:</strong> {error}</li>")
                    full_error_message = "<ul>" + "".join(error_messages) + "</ul>"

                    messages.error(self.request,mark_safe(full_error_message))
            else:
                form = self.form_class()


            context = {'form': form, "form_action_url" :  self.get_form_action_url('create'), 
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.FormName,
            "BreadCrumList" : self.getFormBreadCrumList(),
            "CancelURL" : '/',
            }
            context.update(self.get_extra_context())
            context.update(self.getTableConfig())
            return render(self.request, self.getTemplateName('form'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"BaseCRUDView->create_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    # Update view
   
    def update_view(self, pk):
        try:
            obj = get_object_or_404(self.model, pk=pk)
            if self.request.method == 'POST':
                form = self.form_class(self.request.POST, self.request.FILES, instance=obj)
                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.save()
                    
                    if self.model.__name__ == 'User':

                        if isinstance(obj, self.model):  # only for User model
                            obj.groups.clear()
                            role = form.cleaned_data.get("groups")
                            if role:
                                obj.groups.add(role)
                    
                    messages.success(self.request, f"{self.model._meta.verbose_name} record updated successfully.")
                    form = self.form_class(instance=obj)
                else:
                    # Append all field errors into one message
                    error_messages = []
                    for field, errors in form.errors.items():
                        for error in errors:
                            field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                            error_messages.append(f"<li><strong style='font-size: 14px !important; font-weight: bold !important'>{field_label}:</strong> {error}</li>")
                    full_error_message = "<ul>" + "".join(error_messages) + "</ul>"

                    messages.error(self.request,mark_safe(full_error_message))
                    #messages.error(self.request, "Some fields are missing or incorrect. Please review the form and try again.")
                    
            else:
                form = self.form_class(instance=obj)

            context = {'form': form, 'object': obj, "form_action_url" :  self.get_form_action_url(f'{pk}/update'),
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.FormName,
            "CancelURL" : '/',
            "BreadCrumList" : self.getFormBreadCrumList(obj),
            
                }
            context.update(self.get_extra_context())
            context.update(**self.getTableConfig())
            return render(self.request, self.getTemplateName('form'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"BaseCRUDView->update_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)
    
    # Read only view
    def read_view(self, pk):
        try:
            obj = get_object_or_404(self.model, pk=pk)
            form = self.form_class(instance=obj)
            context = {"form_action_url" :  self.get_form_action_url(f'{pk}/update'),
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.ViewName,
            "BreadCrumList" : self.getReadBreadCrumList(obj),
            "CancelURL" : '/',
            'object' : obj,
            'form' : form
            }
            context.update(self.get_extra_context())
            context.update(self.getTableConfig())
            return render(self.request, self.getTemplateName('view'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"BaseCRUDView->read_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)


    # Delete view
    def delete_view(self, pk):
        try:
            redirect_to = self.request.GET.get('next')
            if redirect_to:
                try:
                    obj = get_object_or_404(self.model, pk=pk)
                    if self.model._meta.verbose_name.lower() == 'user':
                        obj.is_active=False
                    else:
                        obj.status=-1
                    obj.save()
                    messages.success(self.request, f"{obj.get_name} ({obj._meta.verbose_name.title()}) record status changed successfully.")
                except ProtectedError as e:
                    messages.error(self.request, f"This {obj.get_name} ({obj._meta.verbose_name}) record cannot be deleted because it is linked to existing records.")
                except Exception as e:
                    messages.error(self.request, f"Something went wrong: {e}. Please try again later.")
            else:
                messages.error(self.request, f"Invalid Action.")

            return redirect(redirect_to)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"BaseCRUDView->delete_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)
    
    def change_password_view(self, pk):
        try:
            obj = get_object_or_404(self.model, pk=pk)

            # Restrict access
            if self.request.user.pk != obj.pk and not self.request.user.has_perm(f"{self.model._meta.app_label}.can_change_{self.model._meta.model_name}"):
                return HttpResponseForbidden(
                    render(self.request, "core/403.html", {
                        "message": "You don’t have permission to change another user's password."
                    })
                )

            if self.request.method == 'POST':
                form = ChangePasswordForm(user=obj, data=self.request.POST)
                if form.is_valid():
                    user = form.save()
                    update_session_auth_hash(self.request, user)
                    messages.success(self.request, "Password updated successfully!")
                    return redirect(self.get_success_url('list'))
                else:
                    messages.error(self.request, "Please correct the errors below.")
            else:
                form = ChangePasswordForm(user=obj)

            context = {
                'form': form,
                'object': obj,
                "form_action_url": self.get_form_action_url(f"{pk}/changepassword"),
                "model_name": self.model._meta.verbose_name,
                "page_title": "Change Password",
                "BreadCrumList": self.getFormBreadCrumList(obj),
                "CancelURL": '/',
            }
            context.update(self.get_extra_context())
            return render(self.request, "accounts/user_change_password.html", context)

        except Exception as e:
            traceback.print_exc()
            messages.error(self.request, f"Something went wrong: {e}")
            return redirect(self.request.path_info)


class ProductBaseCRUDView(BaseCRUDView): 
    """
    Reusable base class for CRUD operations on any model.

    Usage:
    - Set model, form_class, template names, success_url.
    - Override get_extra_context() for additional context data.
    - Handles pagination, user tracking on create/update.
    """
    # Update view
    
    def update_view(self, pk):
        try:
            obj = get_object_or_404(self.model, pk=pk)
            if self.request.method == 'POST':
                form = self.form_class(self.request.POST, self.request.FILES, instance=obj)
                
                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.save()

                    # Save Product Links
                    ProductLinks.objects.filter(product=obj).delete()
                    for eachURL in self.request.POST.getlist('url'):
                        try:
                            if eachURL.strip():
                                pl_obj = ProductLinks.objects.create(url=eachURL.strip(), product=obj)
                        except Exception as e:
                            print(e)
                    messages.success(self.request, f"{self.model._meta.verbose_name} record updated successfully.")
                    return redirect(self.get_success_url('list'))
                else:
                    # Append all field errors into one message
                    error_messages = []
                    for field, errors in form.errors.items():
                        for error in errors:
                            field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                            error_messages.append(f"<li><strong style='font-size: 14px !important; font-weight: bold !important'>{field_label}:</strong> {error}</li>")
                    full_error_message = "<ul>" + "".join(error_messages) + "</ul>"

                    messages.error(self.request,mark_safe(full_error_message))
                    #messages.error(self.request, "Some fields are missing or incorrect. Please review the form and try again.")
                    
            else:
                form = self.form_class(instance=obj)

            context = {'form': form, 'object': obj, "form_action_url" :  self.get_form_action_url(f'{pk}/update'),
            "model_name" : self.model.__name__ ,
            'page_title': self.FormName,
            "CancelURL" : '/',
            "BreadCrumList" : self.getFormBreadCrumList(obj),
            'object': obj,

                }
            context.update(self.get_extra_context())
            context.update(**self.getTableConfig())
            return render(self.request, self.getTemplateName('form'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"ProductBaseCRUDView->update_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

class CustomUserCRUDView(BaseCRUDView): 
    """
    Reusable base class for CRUD operations on any model.

    Usage:
    - Set model, form_class, template names, success_url.
    - Override get_extra_context() for additional context data.
    - Handles pagination, user tracking on create/update.
    """
    #create_view
    def create_view(self):
        try:
            if self.request.method == 'POST':
                form = self.form_class(self.request.POST, self.request.FILES)

                if form.is_valid():
                    obj = form.save(commit=False)
                    # remove image
                    if form.cleaned_data.get('remove_image'):
                        obj.image.delete(save=False)
                        obj.image=None
                        obj.save()
                    if hasattr(obj, 'created_user'):
                        obj.created_user=self.request.user
                    obj.set_password(settings.USER_DEFAULT_PASSWORD)
                    obj.save()
                    if isinstance(obj, self.model):  # only for User model
                        obj.groups.clear()
                        role = form.cleaned_data.get("groups")
                        if role:
                            obj.groups.add(role)
                    messages.success(self.request, f"{self.model._meta.verbose_name} record created successfully.")
                    return redirect(self.get_success_url('list'))
                else:
                    # error_fields = ', '.join(form.errors.keys())
                    # messages.error(self.request, f"Fields {error_fields} are missing or incorrect. Please review the form and try again.")
                    # Append all field errors into one message
                    error_messages = []
                    for field, errors in form.errors.items():
                        for error in errors:
                            field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                            error_messages.append(f"<li><strong style='font-size: 14px !important; font-weight: bold !important'>{field_label}:</strong> {error}</li>")
                    full_error_message = "<ul>" + "".join(error_messages) + "</ul>"

                    messages.error(self.request,mark_safe(full_error_message))
            else:
                form = self.form_class()


            context = {'form': form, "form_action_url" :  self.get_form_action_url('create'), 
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.FormName,
            "BreadCrumList" : self.getFormBreadCrumList(),
            "CancelURL" : '/',
            }
            context.update(self.get_extra_context())
            context.update(self.getTableConfig())
            return render(self.request, self.getTemplateName('form'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"BaseCRUDView->create_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)
        
    # Update view
    def update_view(self, pk):
        try:
            obj = get_object_or_404(self.model, pk=pk)
            if self.request.method == 'POST':
                form = self.form_class(self.request.POST, self.request.FILES, instance=obj)
                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.save()
                    
                    #if self.model.__name__ == 'User':

                    if isinstance(obj, self.model):  # only for User model
                        obj.groups.clear()
                        role = form.cleaned_data.get("groups")
                        if role:
                            obj.groups.add(role)
                    obj.save()
                    
                    messages.success(self.request, f"{self.model._meta.verbose_name} record updated successfully.")
                    form = self.form_class(instance=obj)
                else:
                    # Append all field errors into one message
                    error_messages = []
                    for field, errors in form.errors.items():
                        for error in errors:
                            field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                            error_messages.append(f"<li><strong style='font-size: 14px !important; font-weight: bold !important'>{field_label}:</strong> {error}</li>")
                    full_error_message = "<ul>" + "".join(error_messages) + "</ul>"

                    messages.error(self.request,mark_safe(full_error_message))
                    #messages.error(self.request, "Some fields are missing or incorrect. Please review the form and try again.")
                    
            else:
                form = self.form_class(instance=obj)

            context = {'form': form, 'object': obj, "form_action_url" :  self.get_form_action_url(f'{pk}/update'),
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.FormName,
            "CancelURL" : '/',
            "BreadCrumList" : self.getFormBreadCrumList(obj),
            
                }
            context.update(self.get_extra_context())
            context.update(**self.getTableConfig())
            return render(self.request, self.getTemplateName('form'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"BaseCRUDView->update_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

class VendorBaseCRUDView(BaseCRUDView): 
    """
    Reusable base class for CRUD operations on any model.

    Usage:
    - Set model, form_class, template names, success_url.
    - Override get_extra_context() for additional context data.
    - Handles pagination, user tracking on create/update.
    """

    def dispatch(self, request, vendor_id, pk=None,  *args, **kwargs):
        """Figure out which CRUD action this is, before calling permission check."""
        self.request = request
        path_end = self.CurReqPath.lower()

        # Detect action
        if path_end.endswith("list"):
            self.action = "list"
        elif path_end.endswith("create"):
            self.action = "create"
        elif pk and path_end.endswith("update"):
            self.action = "update"
        elif pk and path_end.endswith("view"):
            self.action = "view"
        elif pk and path_end.endswith("delete"):
            self.action = "delete"
        else:
            return redirect("home")

        # Assign the method to call later
        self.crud_method = getattr(self, self.CRUD_METHODS[self.action])

        # Now PermissionRequiredMixin will call get_permission_required()
        return super().dispatch(request, vendor_id=vendor_id, pk=pk, *args, **kwargs)
    

    def get(self, request, vendor_id, pk=None, *args, **kwargs):
        """GET routes to list, view, create(form), update(form), delete(confirm)."""
        return self.crud_method(vendor_id, pk) if pk else self.crud_method(vendor_id)

    def post(self, request, vendor_id, pk=None, *args, **kwargs):
        """POST routes to create, update, or delete actions."""
        return self.crud_method(vendor_id, pk) if pk else self.crud_method(vendor_id)

    # Read only view
    def read_view(self, vendor_id, pk):
        try:
            obj = get_object_or_404(self.model, pk=pk)
            vendor_obj = get_object_or_404(Vendor ,pk=vendor_id)
            form = self.form_class(instance=obj)
            context = {"form_action_url" :  self.get_form_action_url(f'{pk}/update'),
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.ViewName,
            "BreadCrumList" : self.getVendorListBreadCrumList(vendor_obj),
            "CancelURL" : '/',
            'object' : obj,
            'form' : form,
            'vendor_obj' : vendor_obj
            }
            context.update(self.get_extra_context())
            context.update(self.getTableConfig())
            return render(self.request, self.getTemplateName('view'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"BaseCRUDView->read_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    # Vendor List view
    def list_view(self, vendor_id):
        try:
            vendor_obj = get_object_or_404(Vendor ,pk=vendor_id)
            queryset = self.getListQuerySet(vendor_id=vendor_id)
            TotalRecords = queryset.count()
            if TotalRecords > 0:
                paginator = Paginator(queryset, self.paginate_by)
                page_obj = paginator.get_page(self.PageNumber)
            else:
                paginator = Paginator([], self.paginate_by)
                page_obj = paginator.get_page(0)


            context = {
                'object_list': page_obj,
                'page_obj': page_obj,
                'paginator': paginator,
                'is_paginated': page_obj.has_other_pages(),
                "model_name" : self.model._meta.verbose_name,
                "RecordsTotal" : TotalRecords,
                "PageNumber" : self.PageNumber,
                'page_title': self.ListName,
                "BreadCrumList" : self.getVendorListBreadCrumList(vendor_obj),
                "CancelURL" : '/',
                'vendor_obj' : vendor_obj,
                "form_status" : False,
                 "PageSizeOptions": [10, 25, 50, 100],
            }
            context.update(self.getTableConfig())
            context.update(self.get_extra_context())
            return render(self.request, self.getTemplateName('list'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"VendorBaseCRUDView->list_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    # Create view
    def create_view(self, vendor_id):
        try:
            vendor_obj = get_object_or_404(Vendor ,pk=vendor_id)
            form_status = True

            if self.request.method == 'POST':
                form = self.form_class(self.request.POST, self.request.FILES)

                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.vendor_id = vendor_id
                    obj.save()
                    form_action_url = self.get_vendor_form_action_url(vendor_id ,'list')
                    messages.success(self.request, f"{self.model._meta.verbose_name} record created successfully.")
                    form_status = False
                    return redirect(
                    self.get_vendor_form_action_url(vendor_id, 'list')
                )
                else:
                    form_action_url = self.get_vendor_form_action_url(vendor_id ,'create')
                    # error_fields = ', '.join(form.errors.keys())
                    # messages.error(self.request, f"Fields {error_fields} are missing or incorrect. Please review the form and try again.")
                    # Append all field errors into one message
                    error_messages = []
                    for field, errors in form.errors.items():
                        for error in errors:
                            field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                            error_messages.append(f"<li><strong style='font-size: 14px !important; font-weight: bold !important'>{field_label}:</strong> {error}</li>")
                    full_error_message = "<ul>" + "".join(error_messages) + "</ul>"

                    messages.error(self.request,mark_safe(full_error_message))
            else:
                form = self.form_class()
                form_action_url = self.get_vendor_form_action_url(vendor_id ,'create')
            
            object_list = self.model.objects.filter(vendor_id=vendor_id)
            context = {'form': form, "form_action_url" : form_action_url,
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.FormName,
            "BreadCrumList" : self.getVendorListBreadCrumList(vendor_obj),
            "CancelURL" : '/',
            'vendor_obj' : vendor_obj,
            'object_list' : object_list,
            'form_status' : form_status
            }
            context.update(self.get_extra_context())
            context.update(self.getTableConfig())
            return render(self.request, self.getTemplateName('list'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"VendorBaseCRUDView->create_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    # Update view
    def update_view(self, vendor_id, pk):
        try:
            vendor_obj = get_object_or_404(Vendor ,pk=vendor_id)
            obj = get_object_or_404(self.model, pk=pk)
            form_status=True
            if self.request.method == 'POST':
                form = self.form_class(self.request.POST, self.request.FILES, instance=obj)
                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.vendor_id = vendor_id
                    obj.save()
                    messages.success(self.request, f"{self.model._meta.verbose_name} record updated successfully.")
                    form = self.form_class()
                    form_status=False
                else:
                    # Append all field errors into one message
                    error_messages = []
                    for field, errors in form.errors.items():
                        for error in errors:
                            field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                            error_messages.append(f"<li><strong style='font-size: 14px !important; font-weight: bold !important'>{field_label}:</strong> {error}</li>")
                    full_error_message = "<ul>" + "".join(error_messages) + "</ul>"

                    messages.error(self.request,mark_safe(full_error_message))
                    #messages.error(self.request, "Some fields are missing or incorrect. Please review the form and try again.")
                    
            else:
                form = self.form_class(instance=obj)
            object_list = self.model.objects.filter(vendor_id=vendor_id)

            context = {'form': form, 'object': obj, "form_action_url" :  self.get_vendor_form_action_url(vendor_id,f'{pk}/update'),
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.FormName,
            "CancelURL" : '/',
            "BreadCrumList" : self.getVendorListBreadCrumList(vendor_obj),
            'vendor_obj' : vendor_obj,
            'object_list' : object_list,
            'form_status' : form_status
                }
            context.update(self.get_extra_context())
            context.update(**self.getTableConfig())
            return render(self.request, self.getTemplateName('list'), context)        
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"VendorBaseCRUDView->update_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    # Delete view
    def delete_view(self, vendor_id, pk):
        try:
            redirect_to = self.request.GET.get('next')
            if redirect_to:
                try:
                    obj = get_object_or_404(self.model, pk=pk)
                    if self.model._meta.verbose_name.lower() == 'user':
                        obj.is_active=False
                    else:
                        obj.status=-1
                    obj.save()
                    messages.success(self.request, f"{obj.get_name} ({obj._meta.verbose_name.title()}) record status changed successfully.")
                except ProtectedError as e:
                    messages.error(self.request, f"This {obj.get_name} ({obj._meta.verbose_name}) record cannot be deleted because it is linked to existing records.")
                except Exception as e:
                    messages.error(self.request, f"Something went wrong: {e}. Please try again later.")
            else:
                messages.error(self.request, f"Invalid Action.")

            return redirect(redirect_to)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"BaseCRUDView->delete_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

class VendorPOBaseCRUDView(BaseCRUDView): 
    """
    Reusable base class for CRUD operations on any model.

    Usage:
    - Set model, form_class, template names, success_url.
    - Override get_extra_context() for additional context data.
    - Handles pagination, user tracking on create/update.
    """

    def dispatch(self, request, po_id, pk=None,  *args, **kwargs):
        """Figure out which CRUD action this is, before calling permission check."""
        self.request = request
        path_end = self.CurReqPath.lower()

        # Detect action
        if path_end.endswith("list"):
            self.action = "list"
        elif path_end.endswith("create"):
            self.action = "create"
        elif pk and path_end.endswith("update"):
            self.action = "update"
        elif pk and path_end.endswith("view"):
            self.action = "view"
        elif pk and path_end.endswith("delete"):
            self.action = "delete"
        else:
            return redirect("home")

        # Assign the method to call later
        self.crud_method = getattr(self, self.CRUD_METHODS[self.action])

        # Now PermissionRequiredMixin will call get_permission_required()
        return super().dispatch(request, po_id=po_id, pk=pk, *args, **kwargs)
    

    def get(self, request, po_id, pk=None, *args, **kwargs):
        """GET routes to list, view, create(form), update(form), delete(confirm)."""
        return self.crud_method(po_id, pk) if pk else self.crud_method(po_id)

    def post(self, request, po_id, pk=None, *args, **kwargs):
        """POST routes to create, update, or delete actions."""
        return self.crud_method(po_id, pk) if pk else self.crud_method(po_id)

    # Read only view
    def read_view(self, po_id, pk):
        try:
            obj = get_object_or_404(self.model, pk=pk)
            po_obj = get_object_or_404(PurchaseOrderHeader, pk=po_id)
            vendor_obj = po_obj.vendor
            form = self.form_class(instance=obj)
            context = {"form_action_url" :  self.get_form_action_url(f'{pk}/update'),
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.ViewName,
            "BreadCrumList" : self.getVendorListBreadCrumList(vendor_obj, po_obj),
            "CancelURL" : '/',
            'object' : obj,
            'form' : form,
            'vendor_obj' : vendor_obj,
            'po_obj' : po_obj
            }
            context.update(self.get_extra_context())
            context.update(self.getTableConfig())
            return render(self.request, self.getTemplateName('view'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"BaseCRUDView->read_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    # Vendor List view
    def list_view(self, po_id):
        try:
            po_obj = get_object_or_404(PurchaseOrderHeader, pk=po_id)
            vendor_obj = po_obj.vendor
            queryset = self.getListQuerySet(vendor_id=vendor_id)
            TotalRecords = queryset.count()
            if TotalRecords > 0:
                paginator = Paginator(queryset, self.paginate_by)
                page_obj = paginator.get_page(self.PageNumber)
            else:
                paginator = Paginator([], self.paginate_by)
                page_obj = paginator.get_page(0)


            context = {
                'object_list': page_obj,
                'page_obj': page_obj,
                'paginator': paginator,
                'is_paginated': page_obj.has_other_pages(),
                "model_name" : self.model._meta.verbose_name,
                "RecordsTotal" : TotalRecords,
                "PageNumber" : self.PageNumber,
                'page_title': self.ListName,
                "BreadCrumList" : self.getVendorListBreadCrumList(vendor_obj, po_obj),
                "CancelURL" : '/',
                'vendor_obj' : vendor_obj,
                "form_status" : False,
                'po_obj' : po_obj
            }
            context.update(self.getTableConfig())
            context.update(self.get_extra_context())
            return render(self.request, self.getTemplateName('list'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"VendorBaseCRUDView->list_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    # Create view
    def create_view(self, po_id):
        try:
            po_obj = get_object_or_404(PurchaseOrderHeader ,pk=po_id)
            vendor_obj = po_obj.vendor
            form_status = True

            if self.request.method == 'POST':
                form = self.form_class(self.request.POST, self.request.FILES)

                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.po_header = po_obj
                    obj.save()
                    messages.success(self.request, f"{self.model._meta.verbose_name} record created successfully.")
                    form_status = False
                    return redirect(reverse('purchase_order_header-view', kwargs={'pk': po_id, 'vendor_id': vendor_obj.pk}))
                else:
                    # error_fields = ', '.join(form.errors.keys())
                    # messages.error(self.request, f"Fields {error_fields} are missing or incorrect. Please review the form and try again.")
                    # Append all field errors into one message
                    error_messages = []
                    for field, errors in form.errors.items():
                        for error in errors:
                            field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                            error_messages.append(f"<li><strong style='font-size: 14px !important; font-weight: bold !important'>{field_label}:</strong> {error}</li>")
                    full_error_message = "<ul>" + "".join(error_messages) + "</ul>"

                    messages.error(self.request,mark_safe(full_error_message))
            else:
                form = self.form_class()

            object_list = self.model.objects.filter(po_header=po_obj)
            context = {'form': form, "form_action_url" :  self.get_vendor_form_action_url(po_id ,'create'),
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.FormName,
            "BreadCrumList" : self.getVendorListBreadCrumList(vendor_obj, po_obj),
            "CancelURL" : '/',
            'vendor_obj' : vendor_obj,
            'object_list' : object_list,
            'form_status' : form_status,
            'po_obj' : po_obj
            }
            context.update(self.get_extra_context())
            context.update(self.getTableConfig())
            return render(self.request, self.getTemplateName('list'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"VendorBaseCRUDView->create_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    # Update view
    def update_view(self, po_id, pk):
        try:
            po_obj = get_object_or_404(PurchaseOrderHeader ,pk=po_id)
            vendor_obj = po_obj.vendor
            obj = get_object_or_404(self.model, pk=pk)
            form_status=True
            if self.request.method == 'POST':
                form = self.form_class(self.request.POST, self.request.FILES, instance=obj)
                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.save()
                    messages.success(self.request, f"{self.model._meta.verbose_name} record updated successfully.")
                    form = self.form_class()
                    form_status=False
                    return redirect(reverse('purchase_order_header-view', kwargs={'pk': po_id, 'vendor_id': vendor_obj.pk}))
                else:
                    # Append all field errors into one message
                    error_messages = []
                    for field, errors in form.errors.items():
                        for error in errors:
                            field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                            error_messages.append(f"<li><strong style='font-size: 14px !important; font-weight: bold !important'>{field_label}:</strong> {error}</li>")
                    full_error_message = "<ul>" + "".join(error_messages) + "</ul>"

                    messages.error(self.request,mark_safe(full_error_message))
                    #messages.error(self.request, "Some fields are missing or incorrect. Please review the form and try again.")
                    
            else:
                form = self.form_class(instance=obj)
            object_list = self.model.objects.filter(po_header=po_id)

            context = {'form': form, 'object': obj, "form_action_url" :  self.get_vendor_form_action_url(po_id,f'{pk}/update'),
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.FormName,
            "CancelURL" : '/',
            "BreadCrumList" : self.getVendorListBreadCrumList(vendor_obj, po_obj),
            'vendor_obj' : vendor_obj,
            'object_list' : object_list,
            'form_status' : form_status,
            'po_obj' : po_obj
                }
            context.update(self.get_extra_context())
            context.update(**self.getTableConfig())
            return render(self.request, self.getTemplateName('list'), context)        
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"VendorBaseCRUDView->update_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    # Delete view
    def delete_view(self, po_id, pk):
        try:
            redirect_to = self.request.GET.get('next')
            if redirect_to:
                try:
                    obj = get_object_or_404(self.model, pk=pk)
                    if self.model._meta.verbose_name.lower() == 'user':
                        obj.is_active=False
                    else:
                        obj.status=-1
                    obj.save()
                    messages.success(self.request, f"{obj.get_name} ({obj._meta.verbose_name.title()}) record status changed successfully.")
                except ProtectedError as e:
                    messages.error(self.request, f"This {obj.get_name} ({obj._meta.verbose_name}) record cannot be deleted because it is linked to existing records.")
                except Exception as e:
                    messages.error(self.request, f"Something went wrong: {e}. Please try again later.")
            else:
                messages.error(self.request, f"Invalid Action.")

            return redirect(redirect_to)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"BaseCRUDView->delete_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

class ProductVendorBaseCRUDView(BaseCRUDView): 
    """
    Reusable base class for CRUD operations on any model.

    Usage:
    - Set model, form_class, template names, success_url.
    - Override get_extra_context() for additional context data.
    - Handles pagination, user tracking on create/update.
    """

    def dispatch(self, request, product_id, pk=None,  *args, **kwargs):
        """Figure out which CRUD action this is, before calling permission check."""
        self.request = request
        path_end = self.CurReqPath.lower()

        # Detect action
        if path_end.endswith("list"):
            self.action = "list"
        elif path_end.endswith("create"):
            self.action = "create"
        elif pk and path_end.endswith("update"):
            self.action = "update"
        elif pk and path_end.endswith("view"):
            self.action = "view"
        elif pk and path_end.endswith("delete"):
            self.action = "delete"
        else:
            return redirect("home")
                   

        # Assign the method to call later
        self.crud_method = getattr(self, self.CRUD_METHODS[self.action])

        # Now PermissionRequiredMixin will call get_permission_required()
        return super().dispatch(request, product_id=product_id, pk=pk, *args, **kwargs)
    

    def get(self, request, product_id, pk=None, *args, **kwargs):
        """GET routes to list, view, create(form), update(form), delete(confirm)."""
        
        return self.crud_method(product_id, pk) if pk else self.crud_method(product_id)

    def post(self, request, product_id, pk=None, *args, **kwargs):
        """POST routes to create, update, or delete actions."""
        return self.crud_method(product_id, pk) if pk else self.crud_method(product_id)

    # Read only view
    def read_view(self, product_id, pk):
        try:
            obj = get_object_or_404(self.model, pk=pk)
            product_vendor_obj = get_object_or_404(Product ,pk=product_id)
            form = self.form_class(instance=obj)
            context = {"form_action_url" :  self.get_form_action_url(f'{pk}/update'),
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.ViewName,
            "BreadCrumList" : self.getReadBreadCrumList(),
            "CancelURL" : '/',
            'object' : obj,
            'form' : form,
            'product_vendor_obj' : product_vendor_obj
            }
            context.update(self.get_extra_context())
            context.update(self.getTableConfig())
            return render(self.request, self.getTemplateName('view'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"BaseCRUDView->read_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)


    # Vendor List view
    def list_view(self, product_id):
        
        try:
            product_obj = get_object_or_404(Product ,pk=product_id)
            queryset = self.getListQuerySet(product_id=product_id)
            TotalRecords = queryset.count()
            if TotalRecords > 0:
                paginator = Paginator(queryset, self.paginate_by)
                page_obj = paginator.get_page(self.PageNumber)
            else:
                paginator = Paginator([], self.paginate_by)
                page_obj = paginator.get_page(0)


            context = {
                'object_list': page_obj,
                'page_obj': page_obj,
                'paginator': paginator,
                'is_paginated': page_obj.has_other_pages(),
                "model_name" : self.model._meta.verbose_name,
                "RecordsTotal" : TotalRecords,
                "PageNumber" : self.PageNumber,
                'page_title': self.ListName,
                "BreadCrumList" : self.getProductVendorListBreadCrumList(product_obj),
                "CancelURL" : '/catalog/product/list',
                'product_obj' : product_obj,
                "form_status" : False
            }
            context.update(self.getTableConfig())
            context.update(self.get_extra_context())

            return render(self.request, self.getTemplateName('list'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"ProductVendorCRUDView->list_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)


    # Create view
    def create_view(self, product_id):
        try:
            product_obj = get_object_or_404(Product ,pk=product_id)
            form_status = True
          

            if self.request.method == 'POST':
                form = self.form_class(self.request.POST, self.request.FILES)

                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.product_id = product_id
                    obj.save()
                    messages.success(self.request, f"{self.model._meta.verbose_name} record created successfully.")
                    form_status = False
                else:
                    # error_fields = ', '.join(form.errors.keys())
                    # messages.error(self.request, f"Fields {error_fields} are missing or incorrect. Please review the form and try again.")
                    # Append all field errors into one message
                    error_messages = []
                    for field, errors in form.errors.items():
                        for error in errors:
                            field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                            error_messages.append(f"<li><strong style='font-size: 14px !important; font-weight: bold !important'>{field_label}:</strong> {error}</li>")
                    full_error_message = "<ul>" + "".join(error_messages) + "</ul>"

                    messages.error(self.request,mark_safe(full_error_message))
            else:
                form = self.form_class()
            #print("form:",form)

            object_list = self.model.objects.filter(product_id=product_id)
            context = {'form': form, "form_action_url" :  self.get_productvendor_form_action_url(product_id ,'create'),
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.FormName,
            "BreadCrumList" : self.getProductVendorListBreadCrumList(product_obj),
            "CancelURL" : '/',
            'product_obj' : product_obj,
            'object_list' : object_list,
            'form_status' : form_status
            }
            context.update(self.get_extra_context())
            context.update(self.getTableConfig())
            
            return render(self.request, self.getTemplateName('list'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"ProductVendorCRUDView->create_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    # Update view
    def update_view(self, product_id, pk):
        try:
            product_obj = get_object_or_404(Product ,pk=product_id)
            obj = get_object_or_404(self.model, pk=pk)
            form_status=True
            if self.request.method == 'POST':
                form = self.form_class(self.request.POST, self.request.FILES, instance=obj)
                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.product_id = product_id
                    obj.save()
                    messages.success(self.request, f"{self.model._meta.verbose_name} record updated successfully.")
                    form = self.form_class()
                    form_status=False
                
                else:
                    # Append all field errors into one message
                    error_messages = []
                    for field, errors in form.errors.items():
                        for error in errors:
                            field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                            error_messages.append(f"<li><strong style='font-size: 14px !important; font-weight: bold !important'>{field_label}:</strong> {error}</li>")
                    full_error_message = "<ul>" + "".join(error_messages) + "</ul>"

                    messages.error(self.request,mark_safe(full_error_message))
                    #messages.error(self.request, "Some fields are missing or incorrect. Please review the form and try again.")
                    
            else:
                form = self.form_class(instance=obj)
            object_list = self.model.objects.filter(product_id=product_id)

            context = {'form': form, 'object': obj, "form_action_url" :  self.get_productvendor_form_action_url(product_id,f'{pk}/update'),
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.FormName,
            "CancelURL" : '/',
            "BreadCrumList" : self.getProductVendorListBreadCrumList(product_obj),
            'product_obj' : product_obj,
            'object_list' : object_list,
            'form_status' : form_status
                }
            context.update(self.get_extra_context())
            context.update(**self.getTableConfig())
            return render(self.request, self.getTemplateName('list'), context)        
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"ProductVendorCRUDView->update_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    # Delete view
    def delete_view(self, product_id, pk):
        try:
            redirect_to = self.request.GET.get('next')
            if redirect_to:
                try:
                    obj = get_object_or_404(self.model, pk=pk)
                    if self.model._meta.verbose_name.lower() == 'user':
                        obj.is_active=False
                    else:
                        obj.status=-1
                        # obj.delete()
                    obj.save()
                    messages.success(self.request, f"{obj.get_name} ({obj._meta.verbose_name.title()}) record status changed successfully.")
                    # messages.success(self.request, f"{obj.get_name} ({obj._meta.verbose_name.title()}) record deleted successfully.")
                except ProtectedError as e:
                    messages.error(self.request, f"This {obj.get_name} ({obj._meta.verbose_name}) record cannot be deleted because it is linked to existing records.")
                except Exception as e:
                    messages.error(self.request, f"Something went wrong: {e}. Please try again later.")
            else:
                messages.error(self.request, f"Invalid Action.")

            return redirect(redirect_to)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"BaseCRUDView->delete_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)            

class FileUploadBaseCRUDView(BaseCRUDView):
    def create_view(self):
        try:
            if self.request.method == "POST":
                form = self.form_class(self.request.POST, self.request.FILES)

                if form.is_valid():
                    obj = form.save(commit=False)

                    # read uploaded excel
                    excel_file = self.request.FILES["file"]

                    # vendor sheet and mandatory/optional fields
                    vendor_df = pd.read_excel(excel_file, sheet_name="Vendors")
                    vendor_mandatory_fields = [
                        "vendor_type_name", "code", "company_name1", "company_name2", "search_keywords",
                        "house_number", "street_name", "phone_number_1", "email_1","country_id", "state", "zipcode"
                    ]
                    vendor_optional_fields = [
                        "dba", "phone_number_2", "phone_number_3", "email_2", "email_3",
                        "payment_terms", "notes", "language_id", "fax", "building_name",
                        "landmark",  "maps_url"
                    ]

                    # vendor bank sheet fields
                    vendor_bank_mandatory_fields = [
                        "account_holder_name", "account_number", "routing_number",
                        "account_type", "bank_name", "branch_name", "ifsc_code", "micr_code"
                    ]
                    vendor_bank_optional_fields = ["swift_code", "address", "primary", "phone_number"]

                    # vendor tax sheet fields
                    vendor_tax_mandatory_fields = ["name", "category", "tax_number", "other_tax_details"]
                    vendor_tax_optional_fields = ["country_id", "tax_rate"]

                    success_records = 0
                    failed_records = 0
                    output_list = []

                    # ---------- Process Vendors ----------
                    for _, row in vendor_df.iterrows():
                        row["status"] = "completed"
                        try:
                            vendor_type = VendorType.objects.get(name=row['vendor_type_name'].strip())
                            # check mandatory vendor fields
                            vendor_mandatory_fields_status = True
                            for field in vendor_mandatory_fields:
                                if pd.isna(row.get(field)) or str(row.get(field)).strip() == "":
                                    vendor_mandatory_fields_status = False
                                    failed_records += 1
                                    break
                            if row['vendor_status'].strip().lower() == 'active':
                                        status = 1
                            elif row['vendor_status'].strip().lower() == 'inactive':
                                status = -1
                            else:
                                status = 0
                            if vendor_mandatory_fields_status:
                                vendor_data = {                         
                                    "vendor_type_id": vendor_type.pk,
                                    "company_name1": row["company_name1"],
                                    "company_name2": row["company_name2"],
                                    "search_keywords": row["search_keywords"],
                                    "house_number": row["house_number"],
                                    "street_name": row["street_name"],
                                    "phone_number_1": row["phone_number_1"],
                                    "email_1": row["email_1"],
                                    "code": row["code"],
                                    "country_id":row['country_id'],
                                    "zipcode":row['zipcode'],
                                    "state":row['state'],
                                    "status": status
                                }

                                # add optional fields if present
                                for field in vendor_optional_fields:
                                    if field in row and pd.notna(row[field]) and str(row[field]).strip() != "":
                                        vendor_data[field] = row[field]

                                # create vendor
                                vendor_obj = Vendor.objects.create(**vendor_data)
                                success_records += 1
                            else:
                                row["status"] = "Failed"

                        except Exception as e:
                            print(str(e))
                            row["status"] = str(e)

                        output_list.append(row)

                    # ---------- Process Vendor Bank Details ----------
                    vb_output_list = []
                    try:
                        vendor_bank_df = pd.read_excel(excel_file, sheet_name="vendor_bank_details")
                    except Exception:
                        vendor_bank_df = pd.DataFrame()  # empty df if sheet not present

                    for _, row in vendor_bank_df.iterrows():
                        row["status"] = "completed"
                        try:
                            vendor_bank_mandatory_fields_status = True
                            for field in vendor_bank_mandatory_fields:
                                if pd.isna(row.get(field)) or str(row.get(field)).strip() == "":
                                    vendor_bank_mandatory_fields_status = False
                                    break

                            if vendor_bank_mandatory_fields_status:
                                vendor_bank_data = {field: row[field] for field in vendor_bank_mandatory_fields}

                                # optional bank fields
                                for field in vendor_bank_optional_fields:
                                    if field in row and pd.notna(row[field]) and str(row[field]).strip() != "":
                                        vendor_bank_data[field] = row[field]

                                # find vendor by company_name1
                                try:
                                    vendor_obj = Vendor.objects.get(company_name1=row.get("vendor_company_name1"))
                                except Vendor.DoesNotExist:
                                    vendor_obj = None

                                if vendor_obj:
                                    vendor_bank_data["vendor_id"] = vendor_obj.pk
                                    VendorBank.objects.create(**vendor_bank_data)
                                else:
                                    row["status"] = "Vendor not exist"
                            else:
                                row["status"] = "Mandatory fields are not there"

                        except Exception as e:
                            row["status"] = str(e)

                        vb_output_list.append(row)

                    # ---------- Process Vendor Tax Details ----------
                    vt_output_list = []
                    try:
                        vendor_tax_df = pd.read_excel(excel_file, sheet_name="vendor_tax_details")
                    except Exception:
                        vendor_tax_df = pd.DataFrame()

                    for _, row in vendor_tax_df.iterrows():
                        row["status"] = "completed"
                        try:
                            vendor_tax_mandatory_fields_status = True
                            for field in vendor_tax_mandatory_fields:
                                if pd.isna(row.get(field)) or str(row.get(field)).strip() == "":
                                    vendor_tax_mandatory_fields_status = False
                                    break

                            if vendor_tax_mandatory_fields_status:
                                vendor_tax_data = {field: row[field] for field in vendor_tax_mandatory_fields}

                                # optional tax fields
                                for field in vendor_tax_optional_fields:
                                    if field in row and pd.notna(row[field]) and str(row[field]).strip() != "":
                                        vendor_tax_data[field] = row[field]

                                # find vendor by company_name1
                                try:
                                    vendor_obj = Vendor.objects.get(company_name1=row.get("vendor_company_name1"))
                                except Vendor.DoesNotExist:
                                    vendor_obj = None

                                if vendor_obj:
                                    vendor_tax_data["vendor_id"] = vendor_obj.pk
                                    VendorTax.objects.create(**vendor_tax_data)
                                else:
                                    row["status"] = "Vendor not exist"
                            else:
                                row["status"] = "Mandatory fields are not there"

                        except Exception as e:
                            row["status"] = str(e)

                        vt_output_list.append(row)

                    # ---------- Save uploaded object and write output workbook ----------
                    obj.save()

                    out_file_path = f"media/uploads/output/output_{obj.pk}.xlsx"
                    os.makedirs(os.path.dirname(out_file_path), exist_ok=True)

                    with pd.ExcelWriter(out_file_path, engine="openpyxl") as writer:
                        if output_list:
                            pd.DataFrame(output_list).to_excel(writer, sheet_name="Vendor", index=False)
                        if vb_output_list:
                            pd.DataFrame(vb_output_list).to_excel(writer, sheet_name="Bank", index=False)
                        if vt_output_list:
                            pd.DataFrame(vt_output_list).to_excel(writer, sheet_name="Tax", index=False)

                    # Attach file to model
                    with open(out_file_path, "rb") as f:
                        obj.output_file.save(f"output_{obj.pk}.xlsx", f)

                    obj.success_records = success_records
                    obj.failed_records = failed_records
                    obj.total_records = success_records + failed_records
                    obj.save()

                    messages.success(self.request, f"{self.model._meta.verbose_name} record created successfully.")
                    return redirect(self.get_success_url("list"))

                else:
                    error_fields = ", ".join(form.errors.keys())
                    messages.error(self.request, f"Fields {error_fields} are missing or incorrect. Please review the form and try again.")
            else:
                form = self.form_class()

            context = {
                "form": form,
                "form_action_url": self.get_form_action_url("create"),
                "model_name": self.model._meta.verbose_name,
                "page_title": self.FormName,
                "BreadCrumList": self.getFormBreadCrumList(),
                "CancelURL": "/",
            }
            context.update(self.get_extra_context())
            context.update(self.getTableConfig())
            return render(self.request, self.getTemplateName("form"), context)

        except Exception as e:
            #traceback.print_exc()
            logger.debug(f"BaseCRUDView->create_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

import os
import time
import zipfile
import logging
import pandas as pd

from io import BytesIO
from PIL import Image

from django.db import transaction
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.safestring import mark_safe
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from ims.models import Units, ProcurementType

logger = logging.getLogger(__name__)

class ProductFileUploadBaseCRUDView(BaseCRUDView):

    def create_view(self):
        start_time = time.time()

        try:
            if self.request.method == 'POST':
                form = self.form_class(self.request.POST, self.request.FILES)

                if form.is_valid():

                    obj = form.save(commit=False)
                    obj.status = "PROCESSING"
                    obj.save()

                    uploaded_file = self.request.FILES['file']

                    logger.info(
                        f"Product Upload Started | File: {uploaded_file.name} | UploadID: {obj.id}"
                    )

                    # --------------------------------------------------
                    # FILE HANDLING (ZIP + Excel + Optional Images)
                    # --------------------------------------------------

                    excel_file = None
                    uploaded_images = {}

                    # CASE 1: ZIP Upload
                    if uploaded_file.name.lower().endswith(".zip"):

                        logger.info("ZIP detected - extracting...")

                        with zipfile.ZipFile(uploaded_file) as zip_ref:

                            for file_name in zip_ref.namelist():

                                if file_name.lower().endswith(".xlsx"):
                                    excel_data = zip_ref.read(file_name)
                                    excel_file = BytesIO(excel_data)

                                if file_name.lower().endswith((".jpg", ".jpeg", ".png", ".pdf", ".doc", ".docx")):

                                    file_data = zip_ref.read(file_name)
                                    file_base = os.path.basename(file_name)

                                    uploaded_images[file_base] = InMemoryUploadedFile(
                                        file=BytesIO(file_data),
                                        field_name=None,
                                        name=file_base,
                                        content_type="application/octet-stream", # image/jpeg and 
                                        size=len(file_data),
                                        charset=None
                                    )


                        if not excel_file:
                            raise Exception("No Excel file found inside ZIP")

                    # CASE 2: Excel Upload
                    else:
                        excel_file = uploaded_file

                        # Check for separately uploaded images
                        for key, file in self.request.FILES.items():
                            if file_name.lower().endswith((".jpg", ".jpeg", ".png", ".pdf", ".doc", ".docx")):
                                uploaded_images[file.name] = file

                    # --------------------------------------------------
                    # READ EXCEL
                    # --------------------------------------------------

                    df = pd.read_excel(excel_file)

                    success_records = 0
                    failed_records = 0
                    output_rows = []
                    error_messages = []
                    warning_messages = []

                    # Ensure India exists
                    india, _ = Country.objects.get_or_create(
                        name="India",
                        defaults={"code": "IN"}
                    )

                    # Preload FK caches
                    product_types = {x.name.lower(): x for x in ProductType.objects.all()}
                    product_groups = {x.name.lower(): x for x in ProductGroup.objects.all()}
                    brands = {x.name.lower(): x for x in Brand.objects.all()}
                    manufacturers = {x.name.lower(): x for x in Manufacturer.objects.all()}
                    languages = {x.name.lower(): x for x in Languages.objects.all()}
                    categories = {x.name.lower(): x for x in Category.objects.all()}
                    units = {x.unit.lower(): x for x in Units.objects.all()}
                    procurement_types = {x.Procurement_name: x for x in ProcurementType.objects.all()}

                    existing_codes = set(
                        Product.objects.values_list("code", flat=True)
                    )

                    status_map = {"active": 1, "inactive": -1, "draft": 0}
                    serial_map = {
                        "yes": 1,
                        "no": 0,
                        "serialized": 1,
                        "non-serialized": 0
                    }

                    def get_or_create_fk(cache, model, name):
                        name = str(name).strip()
                        if not name:
                            raise Exception(f"{model.__name__} is required")
                        key = name.lower()

                        obj = cache.get(key)
                        if not obj:
                            obj = model.objects.create(
                                name=name,
                                code=name[:10].upper()
                            )
                            cache[key] = obj
                            logger.info(f"Auto-created {model.__name__}: {name}")

                        return obj

                    # --------------------------------------------------
                    # PROCESS ROWS
                    # --------------------------------------------------

                    with transaction.atomic():

                        for index, row in df.iterrows():
                            row_number = index + 2
                            row_status = "Completed"

                            try:

                                # Validate Code
                                raw_code = row.get("product_code")

                                if pd.isna(raw_code) or str(raw_code).strip() == "":
                                    raise Exception("Product code is missing")

                                product_code = str(raw_code).strip().upper()

                                if product_code in existing_codes:
                                    raise Exception("Product code already exists")

                                # Validate Name
                                product_name = str(row.get("product_name", "")).strip()
                                if not product_name:
                                    raise Exception("Product name missing")

                                # FK
                                category = get_or_create_fk(categories, Category, row["category_name"])
                                product_type = get_or_create_fk(product_types, ProductType, row["product_type_name"])
                                product_group = get_or_create_fk(product_groups, ProductGroup, row["product_group_name"])
                                brand = get_or_create_fk(brands, Brand, row["brand_name"])
                                manufacturer = get_or_create_fk(manufacturers, Manufacturer, row["manufacturer_name"])
                                language = get_or_create_fk(languages, Languages, row["language_name"])

                                unit_of_measure = get_or_create_fk(units, Units, row["unit_of_measure"])
                                specification = str(row.get("specification")).strip()
                                if not specification:
                                    raise Exception("Specification required")
                                part_no = str(row.get("model_number")).strip()

                                # ProcurementType handled separately
                                procurement_name = str(row.get("procurement_type", "")).strip().lower().capitalize()

                                if not procurement_name:
                                    raise Exception("Procurement Type is required")

                                key = procurement_name

                                procurement_type = procurement_types.get(key)

                                if not procurement_type:
                                    raise Exception(f"Procurement Type '{procurement_name}' not available in system")

                        
                                if not specification:
                                    raise Exception("Specification is required")

                                status = status_map.get(
                                    str(row.get("product_status", "")).strip().lower(), 0
                                )

                                serial_status = serial_map.get(
                                    str(row.get("serialnumber_status", "")).strip().lower(), 0
                                )
                                
                                # Create Product
                                product = Product.objects.create(
                                    name=product_name,
                                    code=product_code,
                                    category=category,
                                    product_type=product_type,
                                    product_group=product_group,
                                    brand=brand,
                                    manufacturer=manufacturer,
                                    language=language,
                                    country=india,
                                    unit_of_measure=unit_of_measure,
                                    procurementtype=procurement_type,
                                    specification=specification,
                                    model_number=part_no,
                                    status=status,
                                    source_of_make=row.get("source_of_make"),
                                    long_description=row.get("long_description"),
                                    short_description=row.get("short_description"),
                                    notes=row.get("notes"),
                                    # Future fields
                                    serialnumber_status=serial_status,
                                    mpin=row.get("mpin"),
                                    upc=row.get("upc"),
                                    isbn=row.get("isbn"),
                                    ean=row.get("ean"),
                                    prefix=row.get("prefix"),
                                    material_code=row.get("material_code"),
                                )

                                existing_codes.add(product_code)

                                # IMAGE (Optional)
                                image_name = row.get("image_file_name")

                                if image_name and str(image_name).strip() != "":
                                    image_name = str(image_name).strip()

                                    image_file = uploaded_images.get(image_name)

                                    if not image_file:

                                        warning_messages.append(
                                            f"Row {row_number}: Image missing ({image_name})"
                                        )

                                    if not image_file:
                                        raise Exception(f"Image not uploaded: {image_name}")

                                    img = Image.open(image_file)
                                    img.thumbnail((800, 800))

                                    buffer = BytesIO()
                                    img.save(buffer, format="JPEG", quality=85)
                                    buffer.seek(0)

                                    product.image.save(
                                        image_name,
                                        ContentFile(buffer.read()),
                                        save=True)
                                # --------------------------------------------------
                                # SPECIFICATION FILE (Optional)
                                # --------------------------------------------------

                                file_name = row.get("specification_file_name")

                                if file_name and str(file_name).strip() != "":
                                    file_name = str(file_name).strip()

                                    spec_file = uploaded_images.get(file_name)

                                    if not spec_file:
                                        raise Exception(f"Specification file not uploaded: {file_name}")

                                    product.file.save(file_name, spec_file, save=True)

                                success_records += 1
                                logger.info(f"Row {row_number} SUCCESS | Code: {product_code}")

                            except Exception as e:
                                failed_records += 1
                                row_status = str(e)

                                error_msg = (
                                    f"Row {row_number} "
                                    f"(Code: {row.get('product_code')}): {row_status}"
                                )

                                logger.error(error_msg)
                                error_messages.append(error_msg)

                            row["upload_status"] = row_status
                            output_rows.append(row)

                    # --------------------------------------------------
                    # SAVE OUTPUT EXCEL
                    # --------------------------------------------------

                    output_df = pd.DataFrame(output_rows)

                    output_path = f"media/uploads/output/product/output_{obj.pk}.xlsx"
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    output_df.to_excel(output_path, index=False)

                    with open(output_path, "rb") as f:
                        obj.output_file.save(
                            f"product_output_{obj.pk}.xlsx", f
                        )

                    obj.success_records = success_records
                    obj.failed_records = failed_records
                    obj.total_records = success_records + failed_records
                    obj.status = "COMPLETED" if failed_records == 0 else "FAILED"
                    obj.save()

                    total_time = round(time.time() - start_time, 2)

                    logger.info(
                        f"Upload Finished | Success: {success_records} | "
                        f"Failed: {failed_records} | Time: {total_time}s"
                    )

                    # ------------------------------
                    # Alerts
                    # ------------------------------

                    if error_messages:

                        messages.error(
                            self.request,
                            mark_safe(
                                "<strong>Upload Completed with Errors</strong><br>"
                                f"Success: {success_records} | Failed: {failed_records}<br><br>"
                                + "<br>".join(error_messages[:10])
                            )
                        )

                    if warning_messages:

                        messages.warning(
                            self.request,
                            mark_safe(
                                "<strong>Upload Completed with Warnings</strong><br>"
                                + "<br>".join(warning_messages[:10])
                            )
                        )

                    if not error_messages and not warning_messages:

                        messages.success(
                            self.request,
                            f"Upload Successful! {success_records} products processed in {total_time} seconds."
                        )

                    return redirect(self.get_success_url('list'))
            else:
                form = self.form_class()

            return render(
                self.request,
                self.getTemplateName('form'),
                {
                    "form": form,
                    "form_action_url": self.get_form_action_url('create'),
                }
            )

        except Exception:
            logger.exception("Critical Error in Product Upload")
            messages.error(self.request, "Unexpected system error occurred.")
            return redirect(self.request.path_info)
        
#------------------------------
# Excel upload only
#------------------------------
        
# import os
# import time
# import pandas as pd
# from django.db import transaction
# from django.shortcuts import render, redirect
# from django.contrib import messages
# from django.utils.safestring import mark_safe
# from django.core.exceptions import ValidationError

# import logging
# logger = logging.getLogger(__name__)


# class ProductFileUploadBaseCRUDView(BaseCRUDView):
#     def create_view(self):
#         start_time = time.time()

#         try:
#             if self.request.method == 'POST':
#                 form = self.form_class(self.request.POST, self.request.FILES)

#                 if form.is_valid():
#                     obj = form.save(commit=False)
#                     obj.status = "PROCESSING"
#                     obj.save()

#                     excel_file = self.request.FILES['file']
#                     logger.info(f"Product Upload Started | File: {excel_file.name} | UploadID: {obj.id}")

#                     df = pd.read_excel(excel_file)

#                     mandatory_fields = [
#                         "product_name",
#                         "product_code",
#                         "category_name",
#                         "product_type_name",
#                         "brand_name",
#                         "manufacturer_name",
#                         "language_name",
#                         "product_group_name"
#                     ]

#                     optional_fields = [
#                         "long_description", "short_description",
#                         "unit_of_measure", "mpin", "upc",
#                         "isbn", "ean", "notes",
#                         "prefix", "model_number",
#                         "source_of_make", "material_code"
#                     ]

#                     success_records = 0
#                     failed_records = 0
#                     output_rows = []
#                     error_messages = []

#                     # Preload FK tables
#                     product_types = {x.name.lower(): x for x in ProductType.objects.all()}
#                     product_groups = {x.name.lower(): x for x in ProductGroup.objects.all()}
#                     brands = {x.name.lower(): x for x in Brand.objects.all()}
#                     manufacturers = {x.name.lower(): x for x in Manufacturer.objects.all()}
#                     languages = {x.name.lower(): x for x in Languages.objects.all()}
#                     categories = {x.name.lower(): x for x in Category.objects.all()}
#                     countries = {x.name.lower(): x for x in Country.objects.all()}

#                     # Ensure India exists
#                     if "india" not in countries:
#                         india = Country.objects.create(name="India", code="IN")
#                         countries["india"] = india
#                         logger.info("Auto-created default country: India")

#                     status_map = {"Active": 1, "Inactive": -1,"Draft":0}
#                     serial_status_map = {
#                         "yes": 1,
#                         "no": 0,
#                         "serialized": 1,
#                         "non-serialized": 0
#                     }

#                     def get_or_create_fk(cache_dict, model_class, name):
#                         key = name.lower()
#                         obj = cache_dict.get(key)
#                         if not obj:
#                             obj = model_class.objects.create(
#                                 name=name,
#                                 code=name[:10].upper()
#                             )
#                             cache_dict[key] = obj
#                             logger.info(f"Auto-created {model_class.__name__}: {name}")
#                         return obj

#                     # 🔥 PROCESS EACH ROW
#                     for index, row in df.iterrows():
#                         row_number = index + 2  # Excel row
#                         row_status = "Completed"

#                         try:
#                             # Validate mandatory fields
#                             for field in mandatory_fields:
#                                 if pd.isna(row.get(field)) or str(row.get(field)).strip() == "":
#                                     raise Exception(f"{field} is missing")

#                             raw_code = row.get("product_code")
#                             if pd.isna(raw_code) or str(raw_code).strip() == "":
#                                 raise Exception("product_code is missing")

#                             product_code = str(raw_code).strip().upper()

#                             product_type = get_or_create_fk(product_types, ProductType, str(row["product_type_name"]).strip())
#                             product_group = get_or_create_fk(product_groups, ProductGroup, str(row["product_group_name"]).strip())
#                             brand = get_or_create_fk(brands, Brand, str(row["brand_name"]).strip())
#                             manufacturer = get_or_create_fk(manufacturers, Manufacturer, str(row["manufacturer_name"]).strip())
#                             language = get_or_create_fk(languages, Languages, str(row["language_name"]).strip())
#                             category = get_or_create_fk(categories, Category, str(row["category_name"]).strip())
#                             country = countries.get("india")

#                             status = status_map.get(str(row.get("product_status", "")).strip().lower(), 0)
#                             serial_status = serial_status_map.get(
#                                 str(row.get("serialnumber_status", "")).strip().lower(), 0
#                             )

#                             product_data = {
#                                 "name": str(row["product_name"]).strip(),
#                                 "code": product_code,
#                                 "category": category,
#                                 "product_type": product_type,
#                                 "product_group": product_group,
#                                 "brand": brand,
#                                 "manufacturer": manufacturer,
#                                 "language": language,
#                                 "country": country,
#                                 "status": status,
#                                 "serialnumber_status": serial_status,
#                             }

#                             for field in optional_fields:
#                                 if field in row and pd.notna(row[field]):
#                                     product_data[field] = row[field]

#                             existing_product = Product.objects.filter(code__iexact=product_code).first()
#                             # overirde if code is exist
#                             # if existing_product:
#                             #     for key, value in product_data.items():
#                             #         setattr(existing_product, key, value)
#                             #     existing_product.save()
#                             #     logger.info(f"Updated Product | Code: {product_code}")
#                             # else:
#                             #     new_product = Product(**product_data)
#                             #     new_product.save()
#                             #     logger.info(f"Created Product | Code: {product_code}")

#                             existing_product = Product.objects.filter(code__iexact=product_code).first()

#                             if existing_product:
#                                 raise Exception("Product code already exists")

#                             new_product = Product(**product_data)
#                             new_product.save()

#                             success_records += 1

#                         except Exception as e:
#                             failed_records += 1
#                             row_status = str(e)

#                             error_msg = f"Row {row_number} (Code: {row.get('product_code')}): {row_status}"
#                             logger.error(error_msg)
#                             error_messages.append(error_msg)

#                         row["status"] = row_status
#                         output_rows.append(row)

#                     # 🔥 Save output file
#                     output_df = pd.DataFrame(output_rows)
#                     out_path = f"media/uploads/output/product/output_{obj.pk}.xlsx"
#                     os.makedirs(os.path.dirname(out_path), exist_ok=True)
#                     output_df.to_excel(out_path, index=False)

#                     with open(out_path, "rb") as f:
#                         obj.output_file.save(f"product_output_{obj.pk}.xlsx", f)

#                     obj.success_records = success_records
#                     obj.failed_records = failed_records
#                     obj.total_records = success_records + failed_records
#                     obj.status = "COMPLETED" if failed_records == 0 else "FAILED"
#                     obj.save()

#                     total_time = round(time.time() - start_time, 2)
#                     logger.info(
#                         f"Upload Finished | Success: {success_records} | "
#                         f"Failed: {failed_records} | Time: {total_time}s"
#                     )

#                     # 🔥 Frontend Messages
#                     if error_messages:
#                         formatted = "<br>".join(error_messages[:10])
#                         messages.error(
#                             self.request,
#                             mark_safe(
#                                 f"<strong>Upload Completed with Errors</strong><br>"
#                                 f"Success: {success_records} | Failed: {failed_records}<br><br>"
#                                 f"{formatted}"
#                             )
#                         )
#                     else:
#                         messages.success(
#                             self.request,
#                             f"Upload Successful! {success_records} products processed in {total_time} seconds."
#                         )

#                     return redirect(self.get_success_url('list'))

#             else:
#                 form = self.form_class()

#             return render(self.request, self.getTemplateName('form'), {
#                 "form": form,
#                 "form_action_url": self.get_form_action_url('create'),
#             })

#         except Exception:
#             logger.exception("Critical Error in Product Upload")
#             messages.error(self.request, "Unexpected system error occurred.")
#             return redirect(self.request.path_info)
      

# class ProductFileUploadBaseCRUDView(BaseCRUDView):
#     def create_view(self):
#         try:
#             if self.request.method == 'POST':
#                 form = self.form_class(self.request.POST, self.request.FILES)

#                 if form.is_valid():
#                     obj = form.save(commit=False)
#                     # remove image

#                     excel_file = self.request.FILES['file']
#                     #vendor
#                     product_df = pd.read_excel(excel_file)  # reads Excel file

#                     # views/vendor.py (inside VendorUploadView.handle_form loop)
#                     product_mandatory_fields = [
#                          "product_name", "product_code", "category_name", "product_type_name", "brand_name", "manufacturer_name", "language_name", "country_name","product_group_name"
#                     ]
#                     optional_fields =["long_description","short_description","unit_of_measure","mpin","upc","isbn","ean","notes"]
                    
#                     success_records=failed_records=total_records=0
#                     output_list = []
#                     for _, row in product_df.iterrows():
#                         row['status']='completed'
#                         try:
#                             product_mandatory_fields_status=True
#                             for field in product_mandatory_fields:
#                                 if pd.isna(row.get(field)) or str(row.get(field)).strip() == "":
#                                     product_mandatory_fields_status=False
#                                     failed_records+=1
#                                     break
#                             if product_mandatory_fields_status:
#                                 try:
#                                     product_type = ProductType.objects.get(name=row['product_type_name'].strip())
#                                     product_group = ProductGroup.objects.get(name=row['product_group_name'].strip())
#                                     brand_obj = Brand.objects.get(name=row['brand_name'].strip())
#                                     manufacturer_obj = Manufacturer.objects.get(name=row['manufacturer_name'].strip())
#                                     language_obj = Languages.objects.get(name=row['language_name'].strip())                   
#                                     country_obj = Country.objects.get(name=row['country_name'].strip())
#                                     category_obj = Category.objects.get(name=row['category_name'].strip())
#                                     if row['product_status'].strip().lower() == 'active':
#                                         status = 1
#                                     elif row['product_status'].strip().lower() == 'inactive':
#                                         status = -1
#                                     else:
#                                         status = 0
#                                     product_data = {
#                                     "product_group_id":product_group.pk,
#                                     "product_type_id":product_type.pk,
#                                     "category_id":category_obj.pk,
#                                     "manufacturer_id":manufacturer_obj.pk,
#                                     "language_id":language_obj.pk,
#                                     "country_id":country_obj.pk,
#                                     "brand_id":brand_obj.pk,
#                                     "name":row['product_name'].strip().lower(),
#                                     "code":row['product_code'].strip().upper(),
#                                     "status": status
#                                     }
#                                     for field in optional_fields:
#                                         if field in row and pd.notna(row[field]) and str(row[field]).strip() != "":
#                                             product_data[field] = row[field]
#                                     product_obj = Product.objects.create(**product_data)

#                                     success_records += 1
#                                 except Exception as e:
#                                     row['status']=str(e)
#                                     failed_records+=1                               

#                             else:
#                                 failed_records+=1
#                                 row['status']='Mandory fields are missing'

#                         except Exception as e:
#                             failed_records+=1
                            
#                             row['status'] = str(e)
#                         output_list.append(row)
#                     out_df = pd.DataFrame(output_list) 
#                     obj.save()
#                     out_file_path = f"media/uploads/output/product/output_{obj.pk}.xlsx"
#                     os.makedirs(os.path.dirname(out_file_path), exist_ok=True)
#                     #out_df.to_excel(out_file_path, index=False)
#                     with pd.ExcelWriter(out_file_path, engine="openpyxl") as writer:
#                         if output_list:
#                             pd.DataFrame(output_list).to_excel(writer, sheet_name="Vendor", index=False)
                     
#                     # Attach file to model
#                     with open(out_file_path, "rb") as f:
#                         obj.output_file.save(f"product_output_{obj.pk}.xlsx", f)
#                     obj.success_records=success_records
#                     obj.failed_records=failed_records
#                     obj.total_records=success_records+failed_records
#                     obj.save()

#                     messages.success(self.request, f"{self.model._meta.verbose_name} record created successfully.")
#                     return redirect(self.get_success_url('list'))
#                 else:
#                     # error_fields = ', '.join(form.errors.keys())
#                     # messages.error(self.request, f"Fields {error_fields} are missing or incorrect. Please review the form and try again.")
#                     # Append all field errors into one message
#                     error_messages = []
#                     for field, errors in form.errors.items():
#                         for error in errors:
#                             field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
#                             error_messages.append(f"<li><strong style='font-size: 14px !important; font-weight: bold !important'>{field_label}:</strong> {error}</li>")
#                     full_error_message = "<ul>" + "".join(error_messages) + "</ul>"

#                     messages.error(self.request,mark_safe(full_error_message))
#             else:
#                 form = self.form_class()


#             context = {'form': form, "form_action_url" :  self.get_form_action_url('create'), 
#             "model_name" : self.model._meta.verbose_name,
#             'page_title': self.FormName,
#             "BreadCrumList" : self.getFormBreadCrumList(),
#             "CancelURL" : '/',
#             }
#             context.update(self.get_extra_context())
#             context.update(self.getTableConfig())
#             return render(self.request, self.getTemplateName('form'), context)
#         except Exception as e:
#             traceback.print_exc()
#             logger.debug(f"BaseCRUDView->create_view: {self.request.path}, Exception: {e}")
#             messages.error(self.request, "Something went wrong. Please try again later")
#             return redirect(self.request.path_info)

class VendorProductBaseCRUDView(BaseCRUDView): 
    """
    Reusable base class for CRUD operations on any model.

    Usage:
    - Set model, form_class, template names, success_url.
    - Override get_extra_context() for additional context data.
    - Handles pagination, user tracking on create/update.
    """

    def dispatch(self, request, vendor_id, pk=None,  *args, **kwargs):
        """Figure out which CRUD action this is, before calling permission check."""
        self.request = request
        path_end = self.CurReqPath.lower()

        # Detect action
        if path_end.endswith("list"):
            self.action = "list"
        elif path_end.endswith("create"):
            self.action = "create"
        elif pk and path_end.endswith("update"):
            self.action = "update"
        elif pk and path_end.endswith("view"):
            self.action = "view"
        elif pk and path_end.endswith("delete"):
            self.action = "delete"
        else:
            return redirect("home")
        print('self.actio:',self.action)            

        # Assign the method to call later
        self.crud_method = getattr(self, self.CRUD_METHODS[self.action])

        # Now PermissionRequiredMixin will call get_permission_required()
        return super().dispatch(request, vendor_id=vendor_id, pk=pk, *args, **kwargs)
    

    def get(self, request, vendor_id, pk=None, *args, **kwargs):
        """GET routes to list, view, create(form), update(form), delete(confirm)."""
        
        return self.crud_method(vendor_id, pk) if pk else self.crud_method(vendor_id)

    def post(self, request, vendor_id, pk=None, *args, **kwargs):
        """POST routes to create, update, or delete actions."""
        return self.crud_method(vendor_id, pk) if pk else self.crud_method(vendor_id)

    # Read only view
    def read_view(self, vendor_id, pk):
        try:
            obj = get_object_or_404(self.model, pk=pk)
            product_vendor_obj = get_object_or_404(Vendor ,pk=vendor_id)
            form = self.form_class(instance=obj)
            context = {"form_action_url" :  self.get_form_action_url(f'{pk}/update'),
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.ViewName,
            "BreadCrumList" : self.getReadBreadCrumList(),
            "CancelURL" : '/',
            'object' : obj,
            'form' : form,
            'product_vendor_obj' : product_vendor_obj
            }
            context.update(self.get_extra_context())
            context.update(self.getTableConfig())
            return render(self.request, self.getVendorProductTemplateName('view'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"BaseCRUDView->read_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)


    # Vendor List view
    def list_view(self, vendor_id):
        
        try:
            vendor_obj = get_object_or_404(Vendor ,pk=vendor_id)
            queryset = self.getListQuerySet(vendor_id=vendor_id)
            TotalRecords = queryset.count()
            if TotalRecords > 0:
                paginator = Paginator(queryset, self.paginate_by)
                page_obj = paginator.get_page(self.PageNumber)
            else:
                paginator = Paginator([], self.paginate_by)
                page_obj = paginator.get_page(0)


            context = {
                'object_list': page_obj,
                'page_obj': page_obj,
                'paginator': paginator,
                'is_paginated': page_obj.has_other_pages(),
                "model_name" : self.model._meta.verbose_name,
                "RecordsTotal" : TotalRecords,
                "PageNumber" : self.PageNumber,
                'page_title': self.ListName,
                "BreadCrumList" : self.getVendorListBreadCrumList(vendor_obj),
                "CancelURL" : '/vendor/list',
                'vendor_obj' : vendor_obj,
                "form_status" : False
            }
            context.update(self.getTableConfig())
            context.update(self.get_extra_context())

            return render(self.request, self.getVendorProductTemplateName('list'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"ProductVendorCRUDView->list_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)


    # Create view
    def create_view(self, vendor_id):
        try:
            vendor_obj = get_object_or_404(Vendor ,pk=vendor_id)
            form_status = True
          

            if self.request.method == 'POST':
                form = self.form_class(self.request.POST, self.request.FILES)
                print(form)
                if form.is_valid():
                    obj = form.save(commit=False)
                    
                    try:
                        vp_obj = ProductVendor.objects.get(product_id=obj.product_id,vendor_id=vendor_id)
                        messages.error(self.request, f"Vendor to Product mapping completed")
                        form_status = False
                        return redirect(self.request.path_info)
                    except:
                        obj.vendor_id=vendor_id
                        obj.save()
                        messages.success(self.request, f"{self.model._meta.verbose_name} record created successfully.")
                        form_status = False
                   

                else:
                    # error_fields = ', '.join(form.errors.keys())
                    # messages.error(self.request, f"Fields {error_fields} are missing or incorrect. Please review the form and try again.")
                    # Append all field errors into one message
                    error_messages = []
                    for field, errors in form.errors.items():
                        for error in errors:
                            field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                            error_messages.append(f"<li><strong style='font-size: 14px !important; font-weight: bold !important'>{field_label}:</strong> {error}</li>")
                    full_error_message = "<ul>" + "".join(error_messages) + "</ul>"

                    messages.error(self.request,mark_safe(full_error_message))
            else:
                form = self.form_class()
      

            object_list = self.model.objects.filter(vendor_id=vendor_id)
            context = {'form': form, "form_action_url" :  self.get_vendorproduct_form_action_url(vendor_id ,'create'),
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.FormName,
            "BreadCrumList" : self.getVendorListBreadCrumList(vendor_obj),
            "CancelURL" : '/',
            'vendor_obj' : vendor_obj,
            'object_list' : object_list,
            'form_status' : form_status
            }
            context.update(self.get_extra_context())
            context.update(self.getTableConfig())
            
            return render(self.request, self.getVendorProductTemplateName('list'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"VendorProductCRUDView->create_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    # Update view
    def update_view(self, vendor_id, pk):
        try:
            vendor_obj = get_object_or_404(Vendor ,pk=vendor_id)
            obj = get_object_or_404(self.model, pk=pk)
            form_status=True
            if self.request.method == 'POST':
                form = self.form_class(self.request.POST, self.request.FILES, instance=obj)
                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.vendor_id = vendor_id
                    obj.save()
                    messages.success(self.request, f"{self.model._meta.verbose_name} record updated successfully.")
                    form = self.form_class()
                    form_status=False
                
                else:
                    # Append all field errors into one message
                    error_messages = []
                    for field, errors in form.errors.items():
                        for error in errors:
                            field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                            error_messages.append(f"<li><strong style='font-size: 14px !important; font-weight: bold !important'>{field_label}:</strong> {error}</li>")
                    full_error_message = "<ul>" + "".join(error_messages) + "</ul>"

                    messages.error(self.request,mark_safe(full_error_message))
                    #messages.error(self.request, "Some fields are missing or incorrect. Please review the form and try again.")
                    
            else:
                form = self.form_class(instance=obj)
            object_list = self.model.objects.filter(vendor_id=vendor_id)

            context = {'form': form, 'object': obj, "form_action_url" :  self.get_vendorproduct_form_action_url(vendor_id,f'{pk}/update'),
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.FormName,
            "CancelURL" : '/',
            "BreadCrumList" : self.getVendorListBreadCrumList(vendor_obj),
            'vendor_obj' : vendor_obj,
            'object_list' : object_list,
            'form_status' : form_status
                }
            context.update(self.get_extra_context())
            context.update(**self.getTableConfig())
            return render(self.request, self.getVendorProductTemplateName('list'), context)        
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"ProductVendorCRUDView->update_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    # Delete view
    def delete_view(self, vendor_id, pk):
        try:
            redirect_to = self.request.GET.get('next')
            if redirect_to:
                try:
                    obj = get_object_or_404(self.model, pk=pk)
                    if self.model._meta.verbose_name.lower() == 'user':
                        obj.is_active=False
                    else:
                        obj.status=-1
                        # obj.delete()
                    obj.save()
                    messages.success(self.request, f"{obj.get_name} ({obj._meta.verbose_name.title()}) record status changed successfully.")
                    # messages.success(self.request, f"{obj.get_name} ({obj._meta.verbose_name.title()}) record deleted successfully.")
                except ProtectedError as e:
                    messages.error(self.request, f"This {obj.get_name} ({obj._meta.verbose_name}) record cannot be deleted because it is linked to existing records.")
                except Exception as e:
                    messages.error(self.request, f"Something went wrong: {e}. Please try again later.")
            else:
                messages.error(self.request, f"Invalid Action.")

            return redirect(redirect_to)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"BaseCRUDView->delete_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)                                  
             
class ProductAttributesBaseView(BaseCRUDView):
    """
    Reusable base class for CRUD operations on any model.

    Usage:
    - Set model, form_class, template names, success_url.
    - Override get_extra_context() for additional context data.
    - Handles pagination, user tracking on create/update.
    """

    # Dispatch to figure out action
    def dispatch(self, request, product_id, pk=None, *args, **kwargs):
        self.request = request
        path_end = self.CurReqPath.lower()

        # Detect action
        if path_end.endswith("list"):
            self.action = "list"
        elif path_end.endswith("create"):
            self.action = "create"
        elif pk and path_end.endswith("update"):
            self.action = "update"
        elif pk and path_end.endswith("view"):
            self.action = "view"
        elif pk and path_end.endswith("delete"):
            self.action = "delete"
        else:
            return redirect("home")

        self.crud_method = getattr(self, self.CRUD_METHODS[self.action])
        return super().dispatch(request, product_id=product_id, pk=pk, *args, **kwargs)

    # GET and POST routing
    def get(self, request, product_id, pk=None, *args, **kwargs):
        return self.crud_method(product_id, pk) if pk else self.crud_method(product_id)

    def post(self, request, product_id, pk=None, *args, **kwargs):
        return self.crud_method(product_id, pk) if pk else self.crud_method(product_id)

    # READ / VIEW
    def read_view(self, product_id):
        try:
            objs = self.model.objects.filter(product_id=product_id)
            product_obj = get_object_or_404(Product, pk=product_id)
            form = self.form_class(product_id)
            context = {
                "form_action_url": self.get_form_action_url(f"{product_id}/update"),
                "model_name": self.model._meta.verbose_name,
                "page_title": self.ViewName,
                "BreadCrumList": self.getReadBreadCrumList(),
                "CancelURL": "/",
                "object": objs,
                "form": form,
                "product_obj": product_obj
            }
            context.update(self.get_extra_context())
            context.update(self.getTableConfig())
            return render(self.request, self.getTemplateName("view"), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"BaseCRUDView->read_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    # CREATE
    def create_view(self, product_id):
        try:
            product_obj = get_object_or_404(Product, pk=product_id)
            form_status = True

            if self.request.method == 'POST':
                form = self.form_class(product_id, self.request.POST, self.request.FILES)
                if form.is_valid():
                    for key, value in self.request.POST.items():
                        if key.startswith("attr_"):
                            attr_id = key.split("_")[1]
                            self.model.objects.update_or_create(
                                product_id=product_id,
                                attribute_id=attr_id,
                                defaults={"value": value}
                            )
                    messages.success(self.request, f"{self.model._meta.verbose_name} record created successfully.")
                    form_status = False
                else:
                    # error_fields = ', '.join(form.errors.keys())
                    # messages.error(self.request, f"Fields {error_fields} are missing or incorrect.")
                    # Append all field errors into one message
                    error_messages = []
                    for field, errors in form.errors.items():
                        for error in errors:
                            field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                            error_messages.append(f"<li><strong style='font-size: 14px !important; font-weight: bold !important'>{field_label}:</strong> {error}</li>")
                    full_error_message = "<ul>" + "".join(error_messages) + "</ul>"

                    messages.error(self.request,mark_safe(full_error_message))

            else:
                form = self.form_class(product_id)

            object_list = self.model.objects.filter(product_id=product_id)
            context = {
                'form': form,
                "form_action_url": self.get_productvendor_form_action_url(product_id, 'create'),
                "model_name": self.model._meta.verbose_name,
                'page_title': self.FormName,
                "BreadCrumList": self.getProductVendorListBreadCrumList(product_obj),
                "CancelURL": '/',
                'product_obj': product_obj,
                'object_list': object_list,
                'form_status': form_status
            }
            context.update(self.get_extra_context())
            context.update(self.getTableConfig())
            return render(self.request, self.getTemplateName('form'), context)

        except Exception as e:
            traceback.print_exc()
            logger.debug(f"ProductAttributesBaseView->create_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    # UPDATE
    def update_view(self, product_id):
        try:
            product_obj = get_object_or_404(Product, pk=product_id)
            form_status = True

            if self.request.method == 'POST':
                form = self.form_class(product_id, self.request.POST, self.request.FILES)
                if form.is_valid():
                    for key, value in self.request.POST.items():
                        if key.startswith("attr_"):
                            attr_id = key.split("_")[1]
                            self.model.objects.update_or_create(
                                product_id=product_id,
                                attribute_id=attr_id,
                                defaults={"value": value}
                            )
                    messages.success(self.request, f"{self.model._meta.verbose_name} record updated successfully.")
                    form_status = False
                else:
                    # error_fields = ', '.join(form.errors.keys())
                    # messages.error(self.request, f"Fields {error_fields} are missing or incorrect.")
                    # Append all field errors into one message
                    error_messages = []
                    for field, errors in form.errors.items():
                        for error in errors:
                            field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                            error_messages.append(f"<li><strong style='font-size: 14px !important; font-weight: bold !important'>{field_label}:</strong> {error}</li>")
                    full_error_message = "<ul>" + "".join(error_messages) + "</ul>"

                    messages.error(self.request,mark_safe(full_error_message))
            else:
                form = self.form_class(product_id)

            object_list = self.model.objects.filter(product_id=product_id)
            context = {
                'form': form,
                "form_action_url": self.get_productvendor_form_action_url(product_id, 'update'),
                "model_name": self.model._meta.verbose_name,
                'page_title': self.FormName,
                "BreadCrumList": self.getProductVendorListBreadCrumList(product_obj),
                "CancelURL": '/',
                'product_obj': product_obj,
                'object_list': object_list,
                'form_status': form_status
            }
            context.update(self.get_extra_context())
            context.update(self.getTableConfig())
            return render(self.request, self.getTemplateName('form'), context)

        except Exception as e:
            traceback.print_exc()
            logger.debug(f"ProductAttributesBaseView->update_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    # LIST
    def list_view(self, product_id):
        self.paginate_by = 100
        try:
            product_obj = get_object_or_404(Product, pk=product_id)
            queryset = self.model.objects.filter(product_id=product_id)
            TotalRecords = queryset.count()
            if TotalRecords > 0:
                paginator = Paginator(queryset, self.paginate_by)
                page_obj = paginator.get_page(self.PageNumber)
            else:
                paginator = Paginator([], self.paginate_by)
                page_obj = paginator.get_page(0)
            paginator = Paginator(queryset, self.paginate_by)
            page_obj = paginator.get_page(self.PageNumber)

            context = {
                'object_list': page_obj,
                'page_obj': page_obj,
                'paginator': paginator,
                'is_paginated': page_obj.has_other_pages(),
                "model_name": self.model._meta.verbose_name,
                "RecordsTotal": queryset.count(),
                "PageNumber": self.PageNumber,
                'page_title': self.ListName,
                "BreadCrumList": self.getProductVendorListBreadCrumList(product_obj),
                "CancelURL": '/catalog/product/list',
                'product_obj': product_obj,
                "form_status": False
            }

            # for eachRow in page_obj.object_list:
            #     print("attttt",eachRow.attribute.attribute_type)
            #     if eachRow.attribute.attribute_type == 'Common':
            #         print(eachRow.attribute.name,"<<<====>>>",eachRow.value)
            #     elif eachRow.attribute.attribute_type == 'Category Specific':
            #         print(eachRow.attribute.name,"<<<====>>>",eachRow.value)
            #     else:
            #         print("No Records Found")
            context.update(self.getTableConfig())
            context.update(self.get_extra_context())
            return render(self.request, self.getTemplateName('list'), context)

        except Exception as e:
            traceback.print_exc()
            logger.debug(f"ProductAttributesBaseView->list_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

class GoodsReceiverBaseCRUDView(BaseCRUDView):
    
    
    def create_view(self):
        logger.info("Entered GoodsReceiver create_view")
        try:
            form_status = True
            grouped_items = {"OPEN": [], "PARTIAL": [], "CLOSED": []}
            status_order = ["OPEN", "PARTIAL", "CLOSED"]
            po_obj=None
            post_po_obj = 'Records'
            message = ''
            if self.request.method == 'POST':
                logger.debug("POST request received in GoodsReceiver")
                data = self.request.POST
                if data['code']:
                    logger.debug(f"PO code received: {data.get('code')}")
                    po_obj = PurchaseOrderHeader.objects.filter(code=data['code']).first()
                    if po_obj:
                        logger.info(f"Purchase Order found: ID={po_obj.id}")
                        messages.success(self.request, "")
                        # messages.success(self.request, f"{self.model._meta.verbose_name} record fetched successfully.")
                    else:
                        logger.warning(f"No Purchase Order found for code: {data['code']}")
                        post_po_obj='No Records'
                        message = f"No Records Found For {data['code']} "
                        messages.warning(self.request, "")
                        # messages.warning(self.request, f"{self.model._meta.verbose_name} record not exist.")

                    form_status = False
                    form = self.form_class()
                else:
                    # error_fields = ', '.join(form.errors.keys())
                    # messages.error(self.request, f"Fields {error_fields} are missing or incorrect. Please review the form and try again.")
                    # Append all field errors into one message
                    logger.error("Form submitted without required code field")
                    error_messages = []
                    for field, errors in form.errors.items():
                        for error in errors:
                            field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                            error_messages.append(f"<li><strong style='font-size: 14px !important; font-weight: bold !important'>{field_label}:</strong> {error}</li>")
                    full_error_message = "<ul>" + "".join(error_messages) + "</ul>"

                    messages.error(self.request,mark_safe(full_error_message))
            else:
                logger.debug("GET request received in GoodsReceiver")             
                po_id = self.request.GET.get('po_id',None)
                if po_id:
                    logger.info(f"Fetching PO using GET param po_id={po_id}")
                    po_obj = get_object_or_404(PurchaseOrderHeader, pk=po_id)
                else:
                    po_id = self.request.session.pop('last_po_id', None)
                    logger.debug(f"PO ID fetched from session: {po_id}")
                form = self.form_class()
                
            item_errors = self.request.session.pop("item_errors", {})
            ht_items_list = self.request.session.pop("ht_items_list", [])           
            if po_obj:
                logger.info(f"Fetching items for PO ID={po_obj.id}")
                items = po_obj.getItems()
                for item in items:
                    grouped_items[item.item_status].append(item)
                
                logger.debug(
                f"Items grouped: "
                f"OPEN={len(grouped_items['OPEN'])}, "
                f"PARTIAL={len(grouped_items['PARTIAL'])}, "
                f"CLOSED={len(grouped_items['CLOSED'])}"
                )

            context = {'form': form, 
            "model_name" : self.model._meta.verbose_name,
            'page_title': "Goods Receipt",
            "CancelURL" : '/',
            'po_obj' : po_obj ,
            "post_po_obj":post_po_obj,
            "grouped_items": grouped_items,
            "ht_items_list":ht_items_list,
            "status_order": status_order,
            'form_status' : form_status,
            "message":message,
            "item_errors":item_errors
            }
            
            logger.debug("Context prepared for GoodsReceiver create_view")
            context.update(self.get_extra_context())
            context.update(self.getTableConfig())

            logger.info("Rendering Goods Receipt form")
            return render(self.request, self.getGoodsTemplateName('form'), context)
        except Exception as e:
            logger.exception(
                f"GoodsReceiverBaseCRUDView->create_view failed | Path={self.request.path}"
            )
            # traceback.print_exc()
            # logger.debug(f"GoodsReceiverBaseCRUDView->create_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info) 
               
    def update_view(self, pk):
        logger.info(f"Entered GoodsReceiver update_view | pk={pk}")
        try:
            po_obj = get_object_or_404(PurchaseOrderHeader, pk=pk)
            logger.info(f"Purchase Order fetched successfully | ID={po_obj.id}")
            
            form = self.form_class(instance=po_obj)

            context = {'form': form, 'object': po_obj, 
            #"form_action_url" :  self.get_form_action_url(f'{pk}/update'),
            "model_name" : self.model.__name__ ,
            'page_title': self.FormName,
            "CancelURL" : '/',
            'po_obj': po_obj, 
            #"BreadCrumList" : self.getFormBreadCrumList(obj),
                }
            context.update(self.get_extra_context())
            context.update(**self.getTableConfig())

            logger.info("Rendering Goods Receipt update form")
            return render(self.request, self.getGoodsTemplateName('form'), context)
        except Exception as e:
            logger.exception(
                f"GoodsReceiverBaseCRUDView->update_view failed | Path={self.request.path}"
            )
            # traceback.print_exc()
            # logger.debug(f"ProductBaseCRUDView->update_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)            

class QualityManagementBaseCRUDView(BaseCRUDView):    
    
    def create_view(self):
        logger.info("Entered create_view")
        try:
            form_status = True
            grouped_items = {"OPEN": [], "PARTIAL": [], "CLOSED": []}
            status_order = ["OPEN", "PARTIAL", "CLOSED"]
            po_obj=None
            post_po_obj = 'Records'
            message = ''
            if self.request.method == 'POST':
                logger.debug("POST request received")
                data = self.request.POST
                if data['code']:
                    logger.debug(f"PO Code received: {data['code']}")
                    po_obj = PurchaseOrderHeader.objects.filter(code=data['code']).first()
                    if po_obj:
                        logger.info(f"Purchase Order found: {po_obj.id}")
                        messages.success(self.request, "")
                        #messages.success(self.request, f"{self.model._meta.verbose_name} record fetched successfully.")
                    else:
                        logger.warning(f"No Purchase Order found for code: {data['code']}")
                        post_po_obj='No Records'
                        message = f"No Records Found For {data['code']} "
                        #messages.warning(self.request, f"{self.model._meta.verbose_name} record not exist.")
                        messages.warning(self.request, "")
                    form_status = False
                    form = self.form_class()
                else:
                    logger.error("Form submitted without PO code")
                    # Append all field errors into one message
                    error_messages = []
                    for field, errors in form.errors.items():
                        for error in errors:
                            field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                            error_messages.append(f"<li><strong style='font-size: 14px !important; font-weight: bold !important'>{field_label}:</strong> {error}</li>")
                    full_error_message = "<ul>" + "".join(error_messages) + "</ul>"

                    messages.error(self.request,mark_safe(full_error_message))
                    # error_fields = ', '.join(form.errors.keys())
                    # messages.error(self.request, f"Fields {error_fields} are missing or incorrect. Please review the form and try again.")
            else:
                logger.debug("GET request received")       
                po_id = self.request.GET.get('po_id',None)
                if po_id:
                    logger.info(f"Fetching PO by ID: {po_id}")
                    po_obj = get_object_or_404(PurchaseOrderHeader, pk=po_id)
                else:
                    po_id = self.request.session.pop('last_po_id', None)
                    logger.debug(f"PO ID from session: {po_id}")
                form = self.form_class()
                
            item_errors = self.request.session.pop("item_errors", {})
            ht_items_list = self.request.session.pop("ht_items_list", [])      

            if po_obj:
                logger.info(f"Fetching items for PO ID: {po_obj.id}")
                items = po_obj.getItems()
                print(items)
                for item in items:
                    grouped_items[item.item_status].append(item)

            # try:
            #     # Your actual code here, for example:
            #     grouped_items = get_grouped_items()  # Replace this with the actual function or logic
            #     if isinstance(grouped_items, dict):
            #         for row, po_items in grouped_items.items():
            #             for eachItem in po_items:
            #                 print(eachItem)
            # except Exception as e:
            #     print(f"An error occurred: {e}")  # Handle any exceptions here
            # finally:
            #     print("Execution completed.")

            context = {'form': form, 
            "model_name" : self.model._meta.verbose_name,
            'page_title': "Quality Management",
            "CancelURL" : '/',
            'po_obj' : po_obj ,
            "post_po_obj":post_po_obj,
            "grouped_items": grouped_items,
            "ht_items_list":ht_items_list,
            "status_order": status_order,
            'form_status' : form_status,
            "message":message,
            "item_errors":item_errors,
            "rejection_codes":RejectionCode.objects.all().order_by('id')
            }
            
            context.update(self.get_extra_context())
            context.update(self.getTableConfig())

            logger.info("Rendering Quality Management form")
            return render(self.request, self.getQMTemplateName('form'), context)
        except Exception as e:
            logger.exception("Exception occurred in create_view")
            #logger.debug(f"QualityManagementBaseCRUDView->create_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info) 
               
    def update_view(self, pk):
        logger.info(f"Entered update_view with pk={pk}")
        try:
            po_obj = get_object_or_404(PurchaseOrderHeader, pk=pk)
            logger.info(f"Purchase Order fetched: {po_obj.id}")
            
            form = self.form_class(instance=po_obj)

            context = {'form': form, 'object': po_obj, 
            #"form_action_url" :  self.get_form_action_url(f'{pk}/update'),
            "model_name" : self.model.__name__ ,
            'page_title': self.FormName,
            "CancelURL" : '/',
            'po_obj': po_obj, 
            #"BreadCrumList" : self.getFormBreadCrumList(obj),

                }
            context.update(self.get_extra_context())
            context.update(**self.getTableConfig())

            logger.info("Rendering update form")
            return render(self.request, self.getQMTemplateName('form'), context)
        except Exception as e:
            logger.exception("Exception occurred in update_view")
            # traceback.print_exc()
            # logger.debug(f"QualityManagementBaseCRUDView->update_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

# from openpyxl import Workbook
# class POReportBaseCRUDView(BaseCRUDView):
    
#     def create_view(self):
#         try:
#             form_status = True
#             grouped_items = {"OPEN": [], "PARTIAL": [], "CLOSED": []}
#             status_order = ["OPEN", "PARTIAL", "CLOSED"]
#             po_obj=None
#             post_po_obj = 'Records'
#             message = ''
#             if self.request.method == 'POST':
#                 data = self.request.POST

#                 start_date = data["start_date"]
#                 end_date = data["end_date"]
#                 export_type = data.get("export_type", "")

#                 if start_date and end_date:
                    
#                     start_date = make_aware(datetime.strptime(start_date, "%Y-%m-%d"))
#                     end_date = make_aware(datetime.strptime(end_date, "%Y-%m-%d"))
                    

#                     po_obj = PurchaseOrderHeader.objects.filter(
#                         created_at__range=(start_date, end_date)
#                     )


#                     if export_type == "excel":
                        
#                         wb = Workbook()
#                         ws = wb.active
#                         ws.title = "PO Report"

#                         headers = [
#                             "PO Line Number", "Product", "Location", "Sub Location",
#                             "Quantity", "Received", "Pending",
#                             "Passed Inspection", "Rejected Inspection", "Pending Inspection",
#                             "Created Time", "Created User",
#                             "Updated Time", "Updated User"
#                         ]
#                         ws.append(headers)

#                         for po in po_obj:
#                             for item in po.getItems():
#                                 ws.append([
#                                     item.code,
#                                     str(item.item),
#                                     item.po_location.name if item.po_location else "",
#                                     item.sub_location.name if item.sub_location else "",
#                                     item.quantity,
#                                     item.already_received_qty,
#                                     item.yet_to_be_received,
#                                     item.good_qty,
#                                     item.rejected_qty,
#                                     item.total_qty_inspected,
#                                     item.created_at.strftime("%Y-%m-%d %H:%M"),
#                                     str(item.created_user),
#                                     item.updated_at.strftime("%Y-%m-%d %H:%M"),
#                                     str(item.updated_user),
#                                 ])

#                         response = HttpResponse(
#                             content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#                         )
#                         response["Content-Disposition"] = 'attachment; filename="po_report.xlsx"'
#                         wb.save(response)
#                         return response


                    
#                     if po_obj:
#                         messages.success(self.request, "")
#                     else:
#                         post_po_obj='No Records'
#                         message = f"No Records found For "
#                         messages.warning(self.request, "")
#                     form_status = False
#                     form = self.form_class()
#                 else:
#                     error_fields = ', '.join(form.errors.keys())
#                     messages.error(self.request, f"Fields {error_fields} are missing or incorrect. Please review the form and try again.")
#             else:               
#                 po_id = self.request.GET.get('po_id',None)
#                 if po_id:
#                     po_obj = get_object_or_404(PurchaseOrderHeader, pk=po_id)
#                 else:
#                     po_id = self.request.session.pop('last_po_id', None)
#                 form = self.form_class()
                
#             item_errors = self.request.session.pop("item_errors", {})
#             ht_items_list = self.request.session.pop("ht_items_list", [])      

#             if po_obj:
#                 for po_ob in po_obj:
#                     items = po_ob.getItems()
#                     for item in items:
#                         grouped_items[item.item_status].append(item)
#             #print(grouped_items,"grouped_items")
                    
#             context = {'form': form, 
#             "model_name" : self.model._meta.verbose_name,
#             'page_title': "PO Report",
#             "CancelURL" : '/',
#             'po_obj' : po_obj,
#             "post_po_obj":post_po_obj,
#             "grouped_items": grouped_items,
#             "ht_items_list":ht_items_list,
#             "status_order": status_order,
#             'form_status' : form_status,
#             "message":message,
#             "item_errors":item_errors,
#             "start_date": start_date,
#             "end_date": end_date
#             }
            
#             # context.update(self.get_extra_context())
#             # context.update(self.getTableConfig())
#             return render(self.request, self.getPOReportemplateName('form'), context)
#         except Exception as e:
#             traceback.print_exc()
#             logger.debug(f"QualityManagementBaseCRUDView->create_view: {self.request.path}, Exception: {e}")
#             messages.error(self.request, "Something went wrong. Please try again later")
#             return redirect(self.request.path_info) 

from openpyxl import Workbook

class POReportBaseCRUDView(BaseCRUDView):

    def create_view(self):
        try:
            form_status = True
            grouped_items = {"OPEN": [], "PARTIAL": [], "CLOSED": []}
            status_order = ["OPEN", "PARTIAL", "CLOSED"]
            po_obj = None
            post_po_obj = 'Records'
            message = ''
            start_date = ''
            end_date = ''
            export_type = ''

            if self.request.method == 'POST':
                data = self.request.POST
                start_date = data.get("start_date", "")
                end_date = data.get("end_date", "")
                export_type = data.get("export_type", "")

                form = self.form_class()

                if start_date and end_date:
                    start_dt = make_aware(datetime.strptime(start_date, "%Y-%m-%d"))
                    end_dt = make_aware(datetime.strptime(end_date, "%Y-%m-%d"))

                    po_obj = PurchaseOrderHeader.objects.filter(
                        created_at__range=(start_dt, end_dt)
                    )

                    # # === EXPORT EXCEL ===
                    if export_type == "excel":
                        wb = Workbook()
                        ws = wb.active
                        ws.title = "PO Report"

                        headers = [
                            "PO Line Number", "Product", "Location", "Sub Location",
                            "Quantity", "Received", "Pending",
                            "Passed Inspection", "Rejected Inspection", "Pending Inspection",
                            "Created Time", "Created User",
                            "Updated Time", "Updated User"
                        ]
                        ws.append(headers)

                        for po in po_obj:
                            for item in po.getItems():
                                ws.append([
                                    item.code,
                                    str(item.item),
                                    item.po_location.name if item.po_location else "",
                                    item.sub_location.name if item.sub_location else "",
                                    item.quantity,
                                    item.already_received_qty,
                                    item.yet_to_be_received,
                                    item.good_qty,
                                    item.rejected_qty,
                                    item.total_qty_inspected,
                                    item.created_at.strftime("%Y-%m-%d %H:%M") if item.created_at else "",
                                    str(item.created_user) if item.created_user else "",
                                    item.updated_at.strftime("%Y-%m-%d %H:%M") if item.updated_at else "",
                                    str(item.updated_user) if item.updated_user else "",
                                ])

                        response = HttpResponse(
                            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        response["Content-Disposition"] = 'attachment; filename="po_report.xlsx"'
                        wb.save(response)
                        return response

                    # === TABLE VIEW ===
                    if po_obj.exists():
                        #messages.success(self.request, "Records found")
                        message = ""
                        messages.success(self.request, message)
                    else:
                        post_po_obj = 'No Records'
                        # message = "No records found for selected date range"
                        message = ""
                        messages.warning(self.request, message)

                    form_status = False

                else:
                    messages.error(self.request, "Please select both From and To dates")
                    form = self.form_class()

            else:
                # GET request
                po_id = self.request.GET.get('po_id', None)
                if po_id:
                    po_obj = get_object_or_404(PurchaseOrderHeader, pk=po_id)
                else:
                    po_id = self.request.session.pop('last_po_id', None)
                
                start_date = ''
                end_date = ''
                form = self.form_class()

            # Pop session variables
            item_errors = self.request.session.pop("item_errors", {})
            ht_items_list = self.request.session.pop("ht_items_list", [])

            # Group items by status
            if po_obj:
                for po_ob in po_obj:
                    items = po_ob.getItems()
                    for item in items:
                        grouped_items[item.item_status].append(item)

            context = {
                'form': form,
                "model_name": self.model._meta.verbose_name,
                'page_title': "PO Report",
                "CancelURL": '/',
                'po_obj': po_obj,
                "post_po_obj": post_po_obj,
                "grouped_items": grouped_items,
                "ht_items_list": ht_items_list,
                "status_order": status_order,
                'form_status': form_status,
                "message": message,
                "item_errors": item_errors,
                "start_date": start_date,   # <-- preserve dates
                "end_date": end_date,       # <-- preserve dates
            }

            return render(self.request, self.getPOReportemplateName('form'), context)

        except Exception as e:
            traceback.print_exc()
            logger.debug(f"POReportBaseCRUDView->create_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

class ProjectHeaderBaseCRUDView(BaseCRUDView):
    
    def history_view(self, project_id, pk):
        # Safely get the object
        obj = get_object_or_404(self.model, pk=pk)
        request = self.request

        # Get the ContentType for this object
        ct = ContentType.objects.get_for_model(obj)

        # Get audit logs for this object
        queryset = LogEntry.objects.filter(
            content_type=ct,
            object_id=obj.pk  # Django will handle int -> string if needed
        ).select_related("actor", "content_type").order_by("-timestamp")

        # Reuse common audit search logic
        logs, page_obj = self._build_audit_logs(request, queryset)

        context = {
            "object": obj,
            "object_list": logs,
            "page_obj": page_obj,
            "FieldList": self.get_audit_fields(),
            "FieldName": request.GET.get("FieldName"),
            "Keyword": request.GET.get("Keyword", ""),
            "BreadCrumList": self.getAuditListBreadCrumList(),
            "active_tab": "history",
        }

        # Merge extra context and render template
        context.update(self.get_extra_context())
        return render(request, self.getTemplateName('history'), context)
    
    def create_view(self):
        try:
            form_status = True
            grouped_items = {"OPEN": [], "PARTIAL": [], "CLOSED": []}
            status_order = ["OPEN", "PARTIAL", "CLOSED"]
            po_obj = None
            ph_obj = None
            bug_obj = None
            post_po_obj = 'Records'
            message = ''
            form = self.form_class()  # always define form

            if self.request.method == 'POST':
                data = self.request.POST
                code = data.get('code')

                if code:
                    po_obj = Project.objects.filter(project_id=code).first()
                    ph_obj = ProjectHeader.objects.filter(project_id=po_obj.id).first() if po_obj else None
                    bug_obj = BudgetAllocation.objects.filter(project=po_obj).first() if po_obj else None

                    if po_obj:
                        messages.success(self.request, f"{self.model._meta.verbose_name} record fetched successfully.")
                    else:
                        post_po_obj = 'No Records'
                        message = f"No Records Found For {code}"
                        messages.warning(self.request, f"{self.model._meta.verbose_name} record not exist.")

                    form_status = False

                else:
                    # Display form errors
                    error_messages = []
                    for field, errors in form.errors.items():
                        field_label = form.fields[field].label if field in form.fields else field.replace('_', ' ').title()
                        for error in errors:
                            error_messages.append(
                                f"<li><strong style='font-size:14px !important; font-weight:bold !important'>{field_label}:</strong> {error}</li>"
                            )
                    if error_messages:
                        full_error_message = "<ul>" + "".join(error_messages) + "</ul>"
                        messages.error(self.request, mark_safe(full_error_message))

            else:
                po_id = self.request.GET.get('po_id')
                if po_id:
                    po_obj = get_object_or_404(Project, pk=po_id)
                else:
                    po_id = self.request.session.pop('last_po_id', None)

                form = self.form_class()

            item_errors = self.request.session.pop("item_errors", {})
            ht_items_list = self.request.session.pop("ht_items_list", [])

            if po_obj:
                grouped_items = po_obj.getItems()

            context = {
                'form': form,
                "model_name": self.model._meta.verbose_name,
                'page_title': "Project Header",
                "CancelURL": '/',
                'po_obj': po_obj,
                'bug_obj': bug_obj,
                'ph_obj': ph_obj,
                "post_po_obj": post_po_obj,
                "grouped_items": grouped_items,
                "ht_items_list": ht_items_list,
                "status_order": status_order,
                'form_status': form_status,
                "message": message,
                "item_errors": item_errors
            }

            context.update(self.get_extra_context())
            context.update(self.getTableConfig())
            return render(self.request, self.getProjectTemplateName('form'), context)

        except Exception as e:
            traceback.print_exc()
            logger.debug(f"ProjectHeaderBaseCRUDView->create_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)
    
    def update_view(self, pk):
        try:
            po_obj = get_object_or_404(Project, pk=pk)

            if self.request.method == "POST":
                form = self.form_class(self.request.POST, instance=po_obj)

                if form.is_valid():
                    form.save()
                    messages.success(
                        self.request,
                        f"{self.model._meta.verbose_name} updated successfully."
                    )
                    return redirect(self.request.path_info)
                else:
                    # 🔴 Custom Error Message Block
                    error_messages = []
                    for field, errors in form.errors.items():
                        field_label = (
                            form.fields[field].label
                            if field in form.fields
                            else field.replace('_', ' ').title()
                        )
                        for error in errors:
                            error_messages.append(
                                f"<li><strong style='font-size:14px !important; "
                                f"font-weight:bold !important'>{field_label}:</strong> {error}</li>"
                            )

                    if error_messages:
                        full_error_message = "<ul>" + "".join(error_messages) + "</ul>"
                        messages.error(self.request, mark_safe(full_error_message))

            else:
                form = self.form_class(instance=po_obj)

            context = {
                'form': form,
                'object': po_obj,
                "model_name": self.model.__name__,
                'page_title': self.FormName,
                "CancelURL": '/',
                'po_obj': po_obj,
            }
            return render(self.request, self.getProjectTemplateName('form'), context)

        except Exception as e:
            traceback.print_exc()
            logger.debug(f"ProjectHeaderBaseCRUDView->update_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

class VoucherHeaderBaseCRUDView(BaseCRUDView):    
    
    def create_view(self):
        try:
            form_status = True
            grouped_items = {"OPEN": [], "PARTIAL": [], "CLOSED": []}
            status_order = ["OPEN", "PARTIAL", "CLOSED"]
            po_obj=None
            vh_obj=None
            bug_obj=None
            post_po_obj = 'Records'
            message = ''
            
            if self.request.method == 'POST':
                data = self.request.POST
                if data['code']:
                    po_obj = Project.objects.filter(project_id=data['code']).first()
                    vh_obj = VoucherHeader.objects.get(project_id=po_obj.id)
                    if po_obj:
                        messages.success(self.request, "")
                        #messages.success(self.request, f"{self.model._meta.verbose_name} record fetched successfully.")
                    else:
                        post_po_obj='No Records'
                        message = f"No Records Found For {data['code']} "
                        messages.warning(self.request, "")
                        #messages.warning(self.request, f"{self.model._meta.verbose_name} record not exist.")

                    form_status = False
                    form = self.form_class()
                else:
                    # error_fields = ', '.join(form.errors.keys())
                    # messages.error(self.request, f"Fields {error_fields} are missing or incorrect. Please review the form and try again.")
                    error_messages = []
                    for field, errors in form.errors.items():
                        field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                        for error in errors:
                            error_messages.append(
                                f"<li><strong style='font-size:14px !important; font-weight:bold !important'>{field_label}:</strong> {error}</li>"
                            )
                    full_error_message = "<ul>" + "".join(error_messages) + "</ul>"
                    messages.error(self.request, mark_safe(full_error_message))
            else:               
                po_id = self.request.GET.get('po_id',None)
                if po_id:
                    po_obj = get_object_or_404(VoucherHeader, pk=po_id)
                else:
                    po_id = self.request.session.pop('last_po_id', None)
                form = self.form_class()
                
            item_errors = self.request.session.pop("item_errors", {})
            ht_items_list = self.request.session.pop("ht_items_list", [])   
            if vh_obj:
                grouped_items = vh_obj.getItems()
                
            context = {'form': form, 
            "model_name" : self.model._meta.verbose_name,
            'page_title': "Issue Voucher",
            "CancelURL" : '/',
            'vh_obj' : vh_obj,
            'po_obj' : po_obj ,            
            "post_po_obj":post_po_obj,
            "grouped_items": grouped_items,
            "ht_items_list":ht_items_list,
            "status_order": status_order,
            'form_status' : form_status,
            "message":message,
            "item_errors":item_errors
            }
            
            context.update(self.get_extra_context())
            context.update(self.getTableConfig())
            return render(self.request, self.getVoucherTemplateName('form'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"VoucherHeaderBaseCRUDView->create_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info) 
               
    def update_view(self, pk):
        try:
            po_obj = get_object_or_404(VoucherHeader, pk=pk)
            
            form = self.form_class(instance=po_obj)

            context = {'form': form, 'object': po_obj, 
            #"form_action_url" :  self.get_form_action_url(f'{pk}/update'),
            "model_name" : self.model.__name__ ,
            'page_title': self.FormName,
            "CancelURL" : '/',
            'po_obj': po_obj, 
            #"BreadCrumList" : self.getFormBreadCrumList(obj),

                }
            context.update(self.get_extra_context())
            context.update(**self.getTableConfig())
            return render(self.request, self.getVoucherTemplateName('form'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"VoucherHeaderBaseCRUDView->update_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)
   
class BOMHeaderBaseCRUDView(BaseCRUDView):       

    def create_view(self):
        try:
            form_status = True
            grouped_items = {"OPEN": [], "PARTIAL": [], "CLOSED": []}
            status_order = ["OPEN", "PARTIAL", "CLOSED"]
            po_obj = None
            post_po_obj = 'Records'
            message = ''
            form = self.form_class()  # always define form

            if self.request.method == 'POST':
                data = self.request.POST
                code = data.get('code')  # safer than data['code']

                if code:
                    po_obj = BOMHeader.objects.filter(code=code).first()
                    if po_obj:
                        messages.success(
                            self.request,
                            f"{self.model._meta.verbose_name} record fetched successfully."
                        )
                    else:
                        po_obj = None
                        post_po_obj = 'No Records'
                        message = f"No Records Found for {code}"
                        messages.warning(
                            self.request,
                            f"{self.model._meta.verbose_name} record does not exist."
                        )

                    form_status = False
                    form = self.form_class()

                else:
                    # No code submitted, handle form validation
                    form = self.form_class(self.request.POST, self.request.FILES)
                    if form.is_valid():
                        obj = form.save(commit=False)

                        # ⚡ Check for duplicate BOM item before saving
                        if hasattr(obj, 'bom') and hasattr(obj, 'product'):
                            if BOMItem.objects.filter(bom=obj.bom, product=obj.product).exists():
                                messages.error(
                                    self.request,
                                    "This product is already added to the BOM."
                                )
                            else:
                                try:
                                    obj.save()
                                    messages.success(
                                        self.request,
                                        f"{self.model._meta.verbose_name} created successfully."
                                    )
                                    return redirect(self.get_success_url())
                                except Exception:
                                    messages.error(
                                        self.request,
                                        "Something went wrong. Please try again later."
                                    )
                        else:
                            # Generic save for objects without BOM/product
                            try:
                                obj.save()
                                messages.success(
                                    self.request,
                                    f"{self.model._meta.verbose_name} created successfully."
                                )
                                return redirect(self.get_success_url())
                            except Exception:
                                messages.error(
                                    self.request,
                                    "Something went wrong. Please try again later."
                                )
                    else:
                        # Collect and display all field errors
                        error_messages = []
                        for field, errors in form.errors.items():
                            field_label = (
                                form.fields[field].label
                                if field in form.fields
                                else field.replace('_', ' ').title()
                            )
                            for error in errors:
                                error_messages.append(
                                    f"<li><strong style='font-size:14px !important; "
                                    f"font-weight:bold !important'>{field_label}:</strong> {error}</li>"
                                )
                        full_error_message = "<ul>" + "".join(error_messages) + "</ul>"
                        messages.error(self.request, mark_safe(full_error_message))

            else:  # GET request
                po_id = self.request.GET.get('po_id', None)
                if po_id:
                    po_obj = get_object_or_404(BOMHeader, pk=po_id)
                else:
                    po_id = self.request.session.pop('last_po_id', None)
                form = self.form_class()

            # Pop session-stored temporary items
            item_errors = self.request.session.pop("item_errors", {})
            ht_items_list = self.request.session.pop("ht_items_list", [])

            # Populate grouped_items if BOMHeader exists
            if po_obj:
                grouped_items = po_obj.getItems()

            context = {
                'form': form,
                "model_name": self.model._meta.verbose_name,
                'page_title': "BOM Header",
                "CancelURL": '/',
                'po_obj': po_obj,
                "post_po_obj": post_po_obj,
                "grouped_items": grouped_items,
                "ht_items_list": ht_items_list,
                "status_order": status_order,
                'form_status': form_status,
                "message": message,
                "item_errors": item_errors
            }

            context.update(self.get_extra_context())
            context.update(self.getTableConfig())
            return render(self.request, self.getBomTemplateName('form'), context)

        except Exception as e:
            traceback.print_exc()
            logger.debug(
                f"BOMHeaderBaseCRUDView->create_view: {self.request.path}, Exception: {e}"
            )
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    def update_view(self, pk):
        try:
            po_obj = get_object_or_404(BOMHeader, pk=pk)

            if self.request.method == 'POST':
                # Include POST data and FILES for form
                form = self.form_class(self.request.POST, self.request.FILES, instance=po_obj)

                if form.is_valid():
                    form.save()
                    messages.success(
                        self.request,
                        f"{self.model._meta.verbose_name} updated successfully."
                    )
                    return redirect(self.request.path_info)
                else:
                    # Collect and display form errors
                    error_messages = []
                    for field, errors in form.errors.items():
                        field_label = (
                            form.fields[field].label
                            if field in form.fields
                            else field.replace('_', ' ').title()
                        )
                        for error in errors:
                            error_messages.append(
                                f"<li><strong style='font-size:14px !important; font-weight:bold !important'>{field_label}:</strong> {error}</li>"
                            )

                    if error_messages:
                        full_error_message = "<ul>" + "".join(error_messages) + "</ul>"
                        messages.error(self.request, mark_safe(full_error_message))
            else:
                # GET request: load form with instance data
                form = self.form_class(instance=po_obj)

            context = {
                'form': form,
                'object': po_obj,
                "model_name": self.model.__name__,
                'page_title': self.FormName,
                "CancelURL": '/',
                'po_obj': po_obj,
            }

            context.update(self.get_extra_context())
            context.update(self.getTableConfig())

            return render(self.request, self.getBomTemplateName('form'), context)

        except Exception as e:
            traceback.print_exc()
            logger.debug(f"BOMHeaderBaseCRUDView->update_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)       

class InventoryBaseCRUDView(BaseCRUDView): 
    """
    Reusable base class for CRUD operations on any model.

    Usage:
    - Set model, form_class, template names, success_url.
    - Override get_extra_context() for additional context data.
    - Handles pagination, user tracking on create/update.
    """

    def dispatch(self, request, vendor_id, pk=None,  *args, **kwargs):
        """Figure out which CRUD action this is, before calling permission check."""
        self.request = request
        path_end = self.CurReqPath.lower()

        # Detect action
        if path_end.endswith("list"):
            self.action = "list"
        elif path_end.endswith("create"):
            self.action = "create"
        elif pk and path_end.endswith("update"):
            self.action = "update"
        elif pk and path_end.endswith("view"):
            self.action = "view"
        elif pk and path_end.endswith("delete"):
            self.action = "delete"
        else:
            return redirect("home")

        # Assign the method to call later
        self.crud_method = getattr(self, self.CRUD_METHODS[self.action])

        # Now PermissionRequiredMixin will call get_permission_required()
        return super().dispatch(request, vendor_id=vendor_id, pk=pk, *args, **kwargs)
    
    def get(self, request, vendor_id, pk=None, *args, **kwargs):
        """GET routes to list, view, create(form), update(form), delete(confirm)."""
        return self.crud_method(vendor_id, pk) if pk else self.crud_method(vendor_id)

    def post(self, request, vendor_id, pk=None, *args, **kwargs):
        """POST routes to create, update, or delete actions."""
        return self.crud_method(vendor_id, pk) if pk else self.crud_method(vendor_id)

    # Read only view
    def read_view(self, vendor_id, pk):
        try:
            obj = get_object_or_404(self.model, pk=pk)
            vendor_obj = get_object_or_404(Vendor ,pk=vendor_id)
            form = self.form_class(instance=obj)
            context = {"form_action_url" :  self.get_form_action_url(f'{pk}/update'),
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.ViewName,
            "BreadCrumList" : self.getVendorListBreadCrumList(vendor_obj),
            "CancelURL" : '/',
            'object' : obj,
            'form' : form,
            'vendor_obj' : vendor_obj
            }
            context.update(self.get_extra_context())
            context.update(self.getTableConfig())
            return render(self.request, self.getTemplateName('view'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"BaseCRUDView->read_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    # List view
    def list_view(self, vendor_id):
        try:
            vendor_obj = get_object_or_404(Vendor ,pk=vendor_id)
            queryset = self.getListQuerySet(vendor_id=vendor_id)
            TotalRecords = queryset.count()
            if TotalRecords > 0:
                paginator = Paginator(queryset, self.paginate_by)
                page_obj = paginator.get_page(self.PageNumber)
            else:
                paginator = Paginator([], self.paginate_by)
                page_obj = paginator.get_page(0)


            context = {
                'object_list': page_obj,
                'page_obj': page_obj,
                'paginator': paginator,
                'is_paginated': page_obj.has_other_pages(),
                "model_name" : self.model._meta.verbose_name,
                "RecordsTotal" : TotalRecords,
                "PageNumber" : self.PageNumber,
                'page_title': self.ListName,
                "BreadCrumList" : self.getVendorListBreadCrumList(vendor_obj),
                "CancelURL" : '/',
                'vendor_obj' : vendor_obj,
                "form_status" : False
            }
            context.update(self.getTableConfig())
            context.update(self.get_extra_context())
            return render(self.request, self.getTemplateName('list'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"VendorBaseCRUDView->list_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    # Create view
    def create_view(self, vendor_id):
        try:
            vendor_obj = get_object_or_404(Vendor ,pk=vendor_id)
            form_status = True

            if self.request.method == 'POST':
                form = self.form_class(self.request.POST, self.request.FILES)

                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.vendor_id = vendor_id
                    obj.save()
                    messages.success(self.request, f"{self.model._meta.verbose_name} record created successfully.")
                    form_status = False
                else:
                    # error_fields = ', '.join(form.errors.keys())
                    # messages.error(self.request, f"Fields {error_fields} are missing or incorrect. Please review the form and try again.")
                    error_messages = []
                    for field, errors in form.errors.items():
                        field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                        for error in errors:
                            error_messages.append(
                                f"<li><strong style='font-size:14px !important; font-weight:bold !important'>{field_label}:</strong> {error}</li>"
                            )
                    full_error_message = "<ul>" + "".join(error_messages) + "</ul>"
                    messages.error(self.request, mark_safe(full_error_message))
            else:
                form = self.form_class()

            object_list = self.model.objects.filter(vendor_id=vendor_id)
            context = {'form': form, "form_action_url" :  self.get_vendor_form_action_url(vendor_id ,'create'),
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.FormName,
            "BreadCrumList" : self.getVendorListBreadCrumList(vendor_obj),
            "CancelURL" : '/',
            'vendor_obj' : vendor_obj,
            'object_list' : object_list,
            'form_status' : form_status
            }
            context.update(self.get_extra_context())
            context.update(self.getTableConfig())
            return render(self.request, self.getTemplateName('list'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"VendorBaseCRUDView->create_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    # Update view
    def update_view(self, vendor_id, pk):
        try:
            vendor_obj = get_object_or_404(Vendor ,pk=vendor_id)
            obj = get_object_or_404(self.model, pk=pk)
            form_status=True
            if self.request.method == 'POST':
                form = self.form_class(self.request.POST, self.request.FILES, instance=obj)
                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.vendor_id = vendor_id
                    obj.save()
                    messages.success(self.request, f"{self.model._meta.verbose_name} record updated successfully.")
                    form = self.form_class()
                    form_status=False
                else:
                    error_messages = []
                    for field, errors in form.errors.items():
                        field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                        for error in errors:
                            error_messages.append(
                                f"<li><strong style='font-size:14px !important; font-weight:bold !important'>{field_label}:</strong> {error}</li>"
                            )
                    full_error_message = "<ul>" + "".join(error_messages) + "</ul>"
                    messages.error(self.request, mark_safe(full_error_message))
                    #messages.error(self.request, "Some fields are missing or incorrect. Please review the form and try again.")
                    
            else:
                form = self.form_class(instance=obj)
            object_list = self.model.objects.filter(vendor_id=vendor_id)

            context = {'form': form, 'object': obj, "form_action_url" :  self.get_vendor_form_action_url(vendor_id,f'{pk}/update'),
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.FormName,
            "CancelURL" : '/',
            "BreadCrumList" : self.getVendorListBreadCrumList(vendor_obj),
            'vendor_obj' : vendor_obj,
            'object_list' : object_list,
            'form_status' : form_status
                }
            context.update(self.get_extra_context())
            context.update(**self.getTableConfig())
            return render(self.request, self.getTemplateName('list'), context)        
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"VendorBaseCRUDView->update_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    # Delete view
    def delete_view(self, vendor_id, pk):
        try:
            redirect_to = self.request.GET.get('next')
            if redirect_to:
                try:
                    obj = get_object_or_404(self.model, pk=pk)
                    if self.model._meta.verbose_name.lower() == 'user':
                        obj.is_active=False
                    else:
                        obj.status=-1
                    obj.save()
                    messages.success(self.request, f"{obj.get_name} ({obj._meta.verbose_name.title()}) record status changed successfully.")
                except ProtectedError as e:
                    messages.error(self.request, f"This {obj.get_name} ({obj._meta.verbose_name}) record cannot be deleted because it is linked to existing records.")
                except Exception as e:
                    messages.error(self.request, f"Something went wrong: {e}. Please try again later.")
            else:
                messages.error(self.request, f"Invalid Action.")

            return redirect(redirect_to)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"BaseCRUDView->delete_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

class InventorySearchBaseCRUDView(BaseCRUDView):
     

    def globalSearchQuerySet(self, **kwargs):
        try:
            if self.Keyword:
                query_conditions = Q()
                for field in self.model.get_search_fields():
                    query_conditions |= Q(**{f"{field}__icontains": self.Keyword})
                queryset = self.model.objects.filter(query_conditions)
                if kwargs:
                    queryset = queryset.filter(**kwargs)
            else:
                queryset = self.model.objects.filter(**kwargs)
        except Exception as e:
            queryset = self.model.objects.none()
            print (e)
        
        return queryset

    def getListQuerySet(self, **kwargs):
        try:
            filter_kwargs = {}
            if self.RecordStatus:
                filter_kwargs.update({self.model.get_status_col_name() : self.RecordStatus})
            
            if self.Keyword and self.FieldName:
                filter_kwargs.update({f"{self.FieldName}__icontains": self.Keyword})
                filter_kwargs.update(kwargs)
                queryset = self.model.objects.filter(**filter_kwargs)
            else:
                if self.RecordStatus:
                    kwargs[self.model.get_status_col_name()] = self.RecordStatus
                queryset = self.globalSearchQuerySet(**kwargs)

            if self.getOrderandSortbyColumn and queryset:
                queryset = queryset.order_by(self.getOrderandSortbyColumn)
        except Exception as e:
            print (e)
            queryset = self.model.objects.all()
        return queryset
    
    def create_view(self):
        try:
            logger.info(
                "Inventory search view accessed | user=%s path=%s method=%s",
                self.request.user,
                self.request.path,
                self.request.method
            )
            form_status = True
            search_query=''
            group_by=''
            results_grouped = {}

            if self.request.method == 'POST':
                form = self.form_class(self.request.POST, self.request.FILES)
                search_query = self.request.POST.get('search_query', '').strip()
                group_by = self.request.POST.get('group_by') or 'product'

                inventories = Inventory.objects.select_related('product', 'location', 'sub_location')
                

                if search_query:
                    # Split query by ',' and strip spaces
                    terms = [t.strip() for t in search_query.split(',') if t.strip()]
                    logger.info("Search terms: %s", terms)
                    for term in terms:

                        inventories_queryset = inventories.filter(
                            Q(product__name__icontains=term) |
                            Q(product__code__icontains=term) |
                            Q(location__name__icontains=term) |
                            Q(location__code__icontains=term) |
                            Q(sub_location__name__icontains=term) |
                            Q(sub_location__code__icontains=term)
                        )

                # group
                if group_by == 'product':
                    for inv in inventories_queryset.order_by('product__name'):
                        total_qty = inventories_queryset.filter(product=inv.product).aggregate(total_qty=Sum('quantity'))['total_qty'] or 0
                        issued_qty = inv.issued_qty
                        key = (inv.product.code,inv.product.name,total_qty,inv.product.serialnumber_status, issued_qty)
                        results_grouped.setdefault(key, []).append(inv)
                else:
                    for inv in inventories_queryset.order_by('location__name'):
                        total_qty = inventories_queryset.filter(location=inv.location).aggregate(total_qty=Sum('quantity'))['total_qty'] or 0
                        issued_qty = inv.issued_qty
                        key = (inv.location.code,inv.location.name,total_qty,inv.product.serialnumber_status, issued_qty)
                        results_grouped.setdefault(key, []).append(inv)
                
            else:               
                
                form = self.form_class()
            
            #print(form)
            # if results_grouped:
            #     for key, inventory_list in results_grouped.items():
            #         first_inventory = inventory_list[0]
            #         print(first_inventory,"first_inventory")
            #         # key = list(results_grouped.keys())[0]
            #         # product_code = key[0]
            #         from inventory.models import GoodsMovementItem
            #         c_obj = Product.objects.get(code=first_inventory)
            #         gm_types = GoodsMovementItem.objects.filter(product_id=c_obj.id).exclude(quantity=0).values('gm_type').distinct()
            #         print(gm_types[0],"111111111111111")

            context = {'form': form, 
    
            "model_name" : self.model._meta.verbose_name,
            'page_title': "Inventory Search",
            "CancelURL" : '/',
            'search_query': search_query,
            'group_by': group_by,
            'results_grouped': results_grouped,
            'form_status' : form_status,
            }
            context.update(self.get_extra_context())
            context.update(self.getTableConfig())
            return render(self.request, self.getInventorySearchTemplateName('form'), context)
        except Exception as e:
            logger.exception(
                "Inventory search failed | user=%s path=%s",
                self.request.user,
                self.request.path
            )
            # traceback.print_exc()
            # logger.debug(f"GoodsReceiverBaseCRUDView->create_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)   
             
    def update_view(self, pk):
        try:
            logger.info(
                "Update view accessed | model=%s pk=%s user=%s",
                self.model.__name__,
                pk,
                self.request.user
            )
            po_obj = get_object_or_404(PurchaseOrderHeader, pk=pk)
            
            form = self.form_class(instance=po_obj)

            context = {'form': form, 'object': po_obj, 
            #"form_action_url" :  self.get_form_action_url(f'{pk}/update'),
            "model_name" : self.model.__name__ ,
            'page_title': self.FormName,
            "CancelURL" : '/',
            'po_obj': po_obj, 
            #"BreadCrumList" : self.getFormBreadCrumList(obj),
           

                }
            context.update(self.get_extra_context())
            context.update(**self.getTableConfig())
            return render(self.request, self.getInventorySearchTemplateName('form'), context)
        except Exception as e:
            logger.exception(
                "Update view failed | model=%s pk=%s path=%s",
                self.model.__name__,
                pk,
                self.request.path
            )
            # traceback.print_exc()
            # logger.debug(f"ProductBaseCRUDView->update_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

class ThemeBaseCrudView(BaseCRUDView):

    def delete_view(self,pk):
    
        try:
            redirect_to = self.request.GET.get('next')
            if redirect_to:
                try:
                    obj = get_object_or_404(self.model, pk=pk)
                    if pk!=1:

                        if self.model._meta.verbose_name.lower() == 'user':
                            obj.is_active=False
                        else:
                            obj.status=-1
                        obj.save()
                        messages.success(self.request, f"{obj.get_name} ({obj._meta.verbose_name.title()}) record status changed successfully.")
                    else:
                        messages.error(self.request, f"This {obj.get_name} ({obj._meta.verbose_name}) record cannot be deleted because it is a default record.")

                except ProtectedError as e:
                    messages.error(self.request, f"This {obj.get_name} ({obj._meta.verbose_name}) record cannot be deleted because it is linked to existing records.")
                except Exception as e:
                    messages.error(self.request, f"Something went wrong: {e}. Please try again later.")
            else:
                messages.error(self.request, f"Invalid Action.")

            return redirect(redirect_to)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"BaseCRUDView->delete_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    def update_view(self, pk):
        try:
            obj = get_object_or_404(self.model, pk=pk)
            if self.request.method == 'POST':
                form = self.form_class(self.request.POST, self.request.FILES, instance=obj)
                if form.is_valid():
                    if pk != 1:

                        obj = form.save(commit=False)
                        obj.save()
                        
                        if self.model.__name__ == 'User':

                            if isinstance(obj, self.model):  # only for User model
                                obj.groups.clear()
                                role = form.cleaned_data.get("groups")
                                if role:
                                    obj.groups.add(role)
                        
                        messages.success(self.request, f"{self.model._meta.verbose_name} record updated successfully.")
                        form = self.form_class(instance=obj)
                    else:
                        messages.success(self.request, f" Default record not able to updated.")
                        form = self.form_class(instance=obj)

                else:
                    error_messages = []
                    for field, errors in form.errors.items():
                        field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                        for error in errors:
                            error_messages.append(
                                f"<li><strong style='font-size:14px !important; font-weight:bold !important'>{field_label}:</strong> {error}</li>"
                            )
                    full_error_message = "<ul>" + "".join(error_messages) + "</ul>"
                    messages.error(self.request, mark_safe(full_error_message))
                    # error_fields = ', '.join(form.errors.keys())
                    # messages.error(self.request, f"Fields {error_fields} are missing or incorrect. Please review the form and try again.")
                    
            else:
                form = self.form_class(instance=obj)

            context = {'form': form, 'object': obj, "form_action_url" :  self.get_form_action_url(f'{pk}/update'),
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.FormName,
            "CancelURL" : '/',
            "BreadCrumList" : self.getFormBreadCrumList(obj),
            
                }
            context.update(self.get_extra_context())
            context.update(**self.getTableConfig())
            return render(self.request, self.getTemplateName('form'), context)

        except Exception as e:
            traceback.print_exc()
            logger.debug(f"BaseCRUDView->update_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

class ChangePasswordCRUDView(AccountCRUDView):
    
    
    def change_password_view(self,pk):
        try:
            obj = get_object_or_404(self.model, pk=pk)
            # Get current user role
            user_roles = self.request.user.groups.values_list('name', flat=True)  # Or obj.role if using custom field

            # Role-based permission check
            if 'Administrator' in user_roles:
                # Admin can change any user's password
                allowed = True
            elif 'Staff' in user_roles:
                # Staff can only change their own password
                allowed = self.request.user.pk == obj.pk
            else:
                # Guests cannot change passwords
                allowed = False

            if not allowed:
                return HttpResponseForbidden(
                    render(self.request, "core/403.html", {
                        "message": "You don’t have permission to change this user's password."
                    })
                )
            if self.request.method == 'POST':
                form = self.form_class(user=obj, data=self.request.POST)
                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.save()
                    
                    
                    # Keep the user logged in after password change
                   
                    update_session_auth_hash(self.request, obj)
                    messages.success(self.request, 'Your password was successfully updated!')
                    form = self.form_class(user=obj)
                else:
                    messages.error(self.request, "Some fields are missing or incorrect. Please review the form and try again.")
                    
            else:
                form = self.form_class(user=obj)

            context = {'form': form, 'object': obj, "form_action_url" :  self.get_form_action_url(f'{pk}/changepassword'),
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.FormName,
            "CancelURL" : '/',
            "BreadCrumList" : self.getFormBreadCrumList(obj),
            
                }
            context.update(self.get_extra_context())
            context.update(**self.getTableConfig())
            return render(self.request, self.getTemplateName('change_password'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"BaseCRUDView->update_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

class BOMCRUDView(BaseCRUDView): 
    """
    Reusable base class for CRUD operations on any model.

    Usage:
    - Set model, form_class, template names, success_url.
    - Override get_extra_context() for additional context data.
    - Handles pagination, user tracking on create/update.
    """

    def dispatch(self, request, bom_id, pk=None,  *args, **kwargs):
        """Figure out which CRUD action this is, before calling permission check."""
        self.request = request
        path_end = self.CurReqPath.lower()

        # Detect action
        if path_end.endswith("list"):
            self.action = "list"
        elif path_end.endswith("create"):
            self.action = "create"
        elif pk and path_end.endswith("update"):
            self.action = "update"
        elif pk and path_end.endswith("view"):
            self.action = "view"
        elif pk and path_end.endswith("delete"):
            self.action = "delete"
        else:
            return redirect("home")

        # Assign the method to call later
        self.crud_method = getattr(self, self.CRUD_METHODS[self.action])

        # Now PermissionRequiredMixin will call get_permission_required()
        return super().dispatch(request, bom_id=bom_id, pk=pk, *args, **kwargs)
    

    def get(self, request, bom_id, pk=None, *args, **kwargs):
        """GET routes to list, view, create(form), update(form), delete(confirm)."""
        return self.crud_method(bom_id, pk) if pk else self.crud_method(bom_id)

    def post(self, request, bom_id, pk=None, *args, **kwargs):
        """POST routes to create, update, or delete actions."""
        return self.crud_method(bom_id, pk) if pk else self.crud_method(bom_id)

    # Read only view
    def read_view(self, bom_id, pk):
        try:
            obj = get_object_or_404(self.model, pk=pk)
            bh_obj = get_object_or_404(BOMHeader ,pk=bom_id)
            form = self.form_class(instance=obj)
            context = {"form_action_url" :  self.get_form_action_url(f'{pk}/update'),
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.ViewName,
            "BreadCrumList" : self.getBomListBreadCrumList(bh_obj,obj),
            "CancelURL" : '/',
            'object' : bh_obj,
            'form' : form,
            'bi_obj' : obj
            }
            context.update(self.get_extra_context())
            context.update(self.getTableConfig())
            return render(self.request, self.getTemplateName('view'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"BaseCRUDView->read_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)


    # BOM List view
    def list_view(self, bom_id):
        try:
            bom_obj = get_object_or_404(BOMHeader ,pk=bom_id)
            queryset = self.getListQuerySet(bom_id=bom_id)
            TotalRecords = queryset.count()
            if TotalRecords > 0:
                paginator = Paginator(queryset, self.paginate_by)
                page_obj = paginator.get_page(self.PageNumber)
            else:
                paginator = Paginator([], self.paginate_by)
                page_obj = paginator.get_page(0)


            context = {
                'object_list': page_obj,
                'page_obj': page_obj,
                'paginator': paginator,
                'is_paginated': page_obj.has_other_pages(),
                "model_name" : self.model._meta.verbose_name,
                "RecordsTotal" : TotalRecords,
                "PageNumber" : self.PageNumber,
                'page_title': self.ListName,
                "BreadCrumList" : self.getListBreadCrumList(),
                "CancelURL" : '/',
                'object' : bom_obj,
                "form_status" : False
            }
            context.update(self.getTableConfig())
            context.update(self.get_extra_context())
            return render(self.request, self.getTemplateName('list'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"VendorBaseCRUDView->list_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    # ---------------- Create View ----------------
    def create_view(self, bom_id):
        try:
            bom_obj = get_object_or_404(BOMHeader, pk=bom_id)
            form_status = True

            if self.request.method == 'POST':
                form = self.form_class(self.request.POST, self.request.FILES)

                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.bom_id = bom_id

                    # 🔹 Only check duplicates if model has 'product'
                    if hasattr(obj, 'product'):
                        if self.model.objects.filter(bom_id=bom_id, product=obj.product).exists():
                            messages.error(
                                self.request,
                                "This product is already added to the BOM."
                            )
                        else:
                            obj.save()
                            messages.success(
                                self.request,
                                f"{self.model._meta.verbose_name} record created successfully."
                            )
                            form_status = False
                    else:
                        # Models without 'product' just save
                        obj.save()
                        messages.success(
                            self.request,
                            f"{self.model._meta.verbose_name} record created successfully."
                        )
                        form_status = False

                else:
                    # Display form errors
                    error_messages = []
                    for field, errors in form.errors.items():
                        field_label = (
                            form.fields[field].label
                            if field in form.fields and form.fields[field].label
                            else field.replace('_', ' ').title()
                        )
                        for error in errors:
                            error_messages.append(
                                f"<li><strong style='font-size:14px; font-weight:bold'>{field_label}:</strong> {error}</li>"
                            )
                    messages.error(self.request, mark_safe("<ul>" + "".join(error_messages) + "</ul>"))

            else:
                form = self.form_class()

            object_list = self.model.objects.filter(bom_id=bom_id)
            context = {
                'form': form,
                'form_action_url': self.get_vendor_form_action_url(bom_id, 'create'),
                'model_name': self.model._meta.verbose_name,
                'page_title': self.FormName,
                'BreadCrumList': self.getTabFormBreadCrumList(bom_obj),
                'CancelURL': '/',
                'object': bom_obj,
                'object_list': object_list,
                'form_status': form_status
            }

            context.update(self.get_extra_context())
            context.update(self.getTableConfig())
            return render(self.request, self.getTemplateName('list'), context)

        except Exception as e:
            traceback.print_exc()
            logger.debug(f"BOMCRUDView->create_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    # ---------------- Update View ----------------
    def update_view(self, bom_id, pk):
        try:
            bom_obj = get_object_or_404(BOMHeader, pk=bom_id)
            obj = get_object_or_404(self.model, pk=pk)
            form_status = True

            if self.request.method == 'POST':
                form = self.form_class(self.request.POST, self.request.FILES, instance=obj)

                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.bom_id = bom_id

                    # 🔹 Only check duplicates if model has 'product'
                    if hasattr(obj, 'product'):
                        if self.model.objects.filter(bom_id=bom_id, product=obj.product).exclude(pk=obj.pk).exists():
                            messages.error(
                                self.request,
                                "This product is already added to the BOM."
                            )
                        else:
                            obj.save()
                            messages.success(
                                self.request,
                                f"{self.model._meta.verbose_name} record updated successfully."
                            )
                            form = self.form_class(instance=obj)
                            form_status = False
                    else:
                        # Models without 'product' just save
                        obj.save()
                        messages.success(
                            self.request,
                            f"{self.model._meta.verbose_name} record updated successfully."
                        )
                        form = self.form_class(instance=obj)
                        form_status = False

                else:
                    # Display form errors
                    error_messages = []
                    for field, errors in form.errors.items():
                        field_label = (
                            form.fields[field].label
                            if field in form.fields and form.fields[field].label
                            else field.replace('_', ' ').title()
                        )
                        for error in errors:
                            error_messages.append(
                                f"<li><strong style='font-size:14px; font-weight:bold'>{field_label}:</strong> {error}</li>"
                            )
                    messages.error(self.request, mark_safe("<ul>" + "".join(error_messages) + "</ul>"))

            else:
                form = self.form_class(instance=obj)

            object_list = self.model.objects.filter(bom_id=bom_id)
            context = {
                'form': form,
                'form_action_url': self.get_vendor_form_action_url(bom_id, f'{pk}/update'),
                'model_name': self.model._meta.verbose_name,
                'page_title': self.FormName,
                'CancelURL': '/',
                'BreadCrumList': self.getTabFormBreadCrumList(bom_obj),
                'object': bom_obj,
                'object_list': object_list,
                'form_status': form_status
            }

            context.update(self.get_extra_context())
            context.update(**self.getTableConfig())
            return render(self.request, self.getTemplateName('list'), context)

        except Exception as e:
            traceback.print_exc()
            logger.debug(f"VendorBaseCRUDView->update_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    # Delete view
    def delete_view(self, bom_id, pk):
        try:
            redirect_to = self.request.GET.get('next')
            if redirect_to:
                try:
                    obj = get_object_or_404(self.model, pk=pk)
                    if self.model._meta.verbose_name.lower() == 'user':
                        obj.is_active=False
                    else:
                        obj.status=-1
                    obj.save()
                    messages.success(self.request, f"{obj.get_name} ({obj._meta.verbose_name.title()}) record status changed successfully.")
                except ProtectedError as e:
                    messages.error(self.request, f"This {obj.get_name} ({obj._meta.verbose_name}) record cannot be deleted because it is linked to existing records.")
                except Exception as e:
                    messages.error(self.request, f"Something went wrong: {e}. Please try again later.")
            else:
                messages.error(self.request, f"Invalid Action.")

            return redirect(redirect_to)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"BaseCRUDView->delete_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

class ProjectBaseCRUDView(BaseCRUDView): 
    """
    Reusable base class for CRUD operations on any model.

    Usage:
    - Set model, form_class, template names, success_url.
    - Override get_extra_context() for additional context data.
    - Handles pagination, user tracking on create/update.
    """

    def dispatch(self, request, project_id, pk=None,  *args, **kwargs):
        """Figure out which CRUD action this is, before calling permission check."""
        self.request = request
        path_end = self.CurReqPath.lower()

        # Detect action
        if path_end.endswith("list"):
            self.action = "list"
        elif path_end.endswith("create"):
            self.action = "create"
        elif pk and path_end.endswith("update"):
            self.action = "update"
        elif pk and path_end.endswith("view"):
            self.action = "view"
        elif pk and path_end.endswith("delete"):
            self.action = "delete"
        elif pk and path_end.endswith("history"):
            self.action = "history"
        else:
            return redirect("home")

        # Assign the method to call later
        self.crud_method = getattr(self, self.CRUD_METHODS[self.action])

        # Now PermissionRequiredMixin will call get_permission_required()
        return super().dispatch(request, project_id=project_id, pk=pk, *args, **kwargs)
    

    def get(self, request, project_id, pk=None, *args, **kwargs):
        """GET routes to list, view, create(form), update(form), delete(confirm)."""
        return self.crud_method(project_id, pk) if pk else self.crud_method(project_id)

    def post(self, request, project_id, pk=None, *args, **kwargs):
        """POST routes to create, update, or delete actions."""
        return self.crud_method(project_id, pk) if pk else self.crud_method(project_id)
    
    def history_view(self, project_id,pk):
        obj = get_object_or_404(self.model, pk=pk)
        project_obj = get_object_or_404(ProjectHeader ,pk=project_id)
        request = self.request

        ct = ContentType.objects.get_for_model(obj)

        queryset = LogEntry.objects.filter(
            content_type=ct,
            object_id=str(obj.pk)
        ).select_related(
            "actor", "content_type"
        ).order_by("-timestamp")

        # reuse common audit search logic
        logs, page_obj = self._build_audit_logs(request, queryset)

        context = {
            "object": obj,
            "object_list": logs,
            "page_obj": page_obj,
            "FieldList": self.get_audit_fields(),
            "FieldName": request.GET.get("FieldName"),
            "Keyword": request.GET.get("Keyword",''),
             "BreadCrumList" : self.getBomListBreadCrumList(project_obj,obj),
            "active_tab": "history",
        }

        #return render(request, self.audit_template_name, context)
        #context.update(self.getTableConfig())
        context.update(self.get_extra_context())
        return render(self.request, self.getTemplateName('history'), context)
    
    # Read only view
    def read_view(self, project_id, pk):
        try:
            obj = get_object_or_404(self.model, pk=pk)
            project_obj = get_object_or_404(ProjectHeader ,pk=project_id)

            form = self.form_class(project_obj,instance=obj)
            context = {"form_action_url" :  self.get_form_action_url(f'{pk}/update'),
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.ViewName,
            "BreadCrumList" : self.getBomListBreadCrumList(project_obj,obj),
            "CancelURL" : '/',
            'object' : project_obj,
            'form' : form,
            'project_component_obj' : obj
            }
            context.update(self.get_extra_context())
            context.update(self.getTableConfig())
            return render(self.request, self.getTemplateName('view'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"PROJECTBASECRUDView->read_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)


    # Vendor List view
    def list_view(self, project_id):
        try:
            project_obj = get_object_or_404(ProjectHeader ,pk=project_id)
            queryset = self.getListQuerySet(project_id=project_id)
            TotalRecords = queryset.count()
            if TotalRecords > 0:
                paginator = Paginator(queryset, self.paginate_by)
                page_obj = paginator.get_page(self.PageNumber)
            else:
                paginator = Paginator([], self.paginate_by)
                page_obj = paginator.get_page(0)


            context = {
                'object_list': page_obj,
                'page_obj': page_obj,
                'paginator': paginator,
                'is_paginated': page_obj.has_other_pages(),
                "model_name" : self.model._meta.verbose_name,
                "RecordsTotal" : TotalRecords,
                "PageNumber" : self.PageNumber,
                'page_title': self.ListName,
                "BreadCrumList" : self.getProjectBreadCrumList(project_obj),
                "CancelURL" : '/',
                'object' : project_obj,
                "form_status" : False
            }
            context.update(self.getTableConfig())
            context.update(self.get_extra_context())
            return render(self.request, self.getTemplateName('list'), context)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"PROJECTBASECRUDView->list_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    # Create view
    def create_view(self, project_id):
        try:
            project_obj = get_object_or_404(ProjectHeader, pk=project_id)
            form_status = True
            obj = None

            if self.request.method == 'POST':
                form = self.form_class(project_obj, self.request.POST, self.request.FILES)

                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.project_id = project_id

                    try:
                        obj.save()

                        messages.success(
                            self.request,
                            f"{self.model._meta.verbose_name} record created successfully."
                        )
                        form_status = False

                    except IntegrityError:
                        form.add_error(
                            None,
                            f"{self.model._meta.verbose_name} already exists."
                        )

                else:
                    # error_fields = ', '.join(form.errors.keys())
                    # messages.error(
                    #     self.request,
                    #     f"Fields {error_fields} are missing or incorrect. Please review the form and try again."
                    # )
                    error_messages = []
                    for field, errors in form.errors.items():
                        field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                        for error in errors:
                            error_messages.append(
                                f"<li><strong style='font-size:14px !important; font-weight:bold !important'>{field_label}:</strong> {error}</li>"
                            )
                    full_error_message = "<ul>" + "".join(error_messages) + "</ul>"
                    messages.error(self.request, mark_safe(full_error_message))
            else:
                form = self.form_class(project_obj)

            object_list = self.model.objects.filter(project_id=project_id)

            context = {
                'form': form,
                "form_action_url": self.get_vendor_form_action_url(project_id, 'create'),
                "model_name": self.model._meta.verbose_name,
                'page_title': self.FormName,
                "BreadCrumList": self.getProjectBreadCrumList(project_obj, obj),
                "CancelURL": '/',
                'object': project_obj,
                'object_list': object_list,
                'form_status': form_status
            }

            context.update(self.get_extra_context())
            context.update(self.getTableConfig())

            return render(self.request, self.getTemplateName('list'), context)

        except Exception as e:
            traceback.print_exc()
            logger.debug(f"PROJECTBASECRUDView->create_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)


    # Update view
    def update_view(self, project_id, pk):
        try:
            project_obj = get_object_or_404(ProjectHeader ,pk=project_id)
            obj = get_object_or_404(self.model, pk=pk)
            form_status=True
            if self.request.method == 'POST':
                
                form = self.form_class(project_obj, self.request.POST, self.request.FILES, instance=obj)
                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.project_id = project_id
                    obj.save()
                    messages.success(self.request, f"{self.model._meta.verbose_name} record updated successfully.")
                    form = self.form_class(project_obj)
                    form_status=False
                else:
                    error_messages = []
                    for field, errors in form.errors.items():
                        field_label = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                        for error in errors:
                            error_messages.append(
                                f"<li><strong style='font-size:14px !important; font-weight:bold !important'>{field_label}:</strong> {error}</li>"
                            )
                    full_error_message = "<ul>" + "".join(error_messages) + "</ul>"
                    messages.error(self.request, mark_safe(full_error_message))
                    #messages.error(self.request, "Some fields are missing or incorrect. Please review the form and try again.")
                    
            else:
                form = self.form_class(project_obj,instance=obj)
            object_list = self.model.objects.filter(project_id=project_id)

            context = {'form': form, 'object': obj, "form_action_url" :  self.get_vendor_form_action_url(project_id,f'{pk}/update'),
            "model_name" : self.model._meta.verbose_name,
            'page_title': self.FormName,
            "CancelURL" : '/',
            "BreadCrumList" : self.getProjectItemBreadCrumList(project_obj,obj),
            'object' : project_obj,
            'object_list' : object_list,
            'form_status' : form_status
                }
            #print(context)
            context.update(self.get_extra_context())
            context.update(**self.getTableConfig())
            return render(self.request, self.getTemplateName('list'), context)        
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"PROJECTBASECRUDView->update_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

    # Delete view
    def delete_view(self, project_id, pk):
        try:
            redirect_to = self.request.GET.get('next')
            if redirect_to:
                try:
                    obj = get_object_or_404(self.model, pk=pk)
                    if self.model._meta.verbose_name.lower() == 'user':
                        obj.is_active=False
                    else:
                        obj.status=-1
                    obj.save()
                    messages.success(self.request, f"{obj.get_name} ({obj._meta.verbose_name.title()}) record status changed successfully.")
                except ProtectedError as e:
                    messages.error(self.request, f"This {obj.get_name} ({obj._meta.verbose_name}) record cannot be deleted because it is linked to existing records.")
                except Exception as e:
                    messages.error(self.request, f"Something went wrong: {e}. Please try again later.")
            else:
                messages.error(self.request, f"Invalid Action.")

            return redirect(redirect_to)
        except Exception as e:
            traceback.print_exc()
            logger.debug(f"PROJECTBASECRUDView->delete_view: {self.request.path}, Exception: {e}")
            messages.error(self.request, "Something went wrong. Please try again later")
            return redirect(self.request.path_info)

class ProjectIssueVoucherCRUDView(BaseCRUDView):
    
    def dispatch(self, request, project_id, pk=None,  *args, **kwargs):
        """Figure out which CRUD action this is, before calling permission check."""
        self.request = request
        path_end = self.CurReqPath.lower()

        # Detect action
        if path_end.endswith("list"):
            self.action = "list"
        elif path_end.endswith("create"):
            self.action = "create"
        elif pk and path_end.endswith("update"):
            self.action = "update"
        elif pk and path_end.endswith("view"):
            self.action = "view"
        elif pk and path_end.endswith("delete"):
            self.action = "delete"
        else:
            return redirect("home")

        # Assign the method to call later
        self.crud_method = getattr(self, self.CRUD_METHODS[self.action])

        # Now PermissionRequiredMixin will call get_permission_required()
        return super().dispatch(request, project_id=project_id, pk=pk, *args, **kwargs)
    

    def get(self, request, project_id, pk=None, *args, **kwargs):
        """GET routes to list, view, create(form), update(form), delete(confirm)."""
        return self.crud_method(project_id, pk) if pk else self.crud_method(project_id)

    def post(self, request, project_id, pk=None, *args, **kwargs):
        """POST routes to create, update, or delete actions."""
        return self.crud_method(project_id, pk) if pk else self.crud_method(project_id)
    



    def generate_issue_voucher_number(self,pr_code):

        fy = str(date.today().year)[-2:]  # 2026 → 26

        last = GoodsMovementHeader.objects.order_by("-id").first()

        if last:
            seq = last.id + 1
        else:
            seq = 1

        seq_str = str(seq).zfill(4)
        
        pr_code = pr_code.replace('0','')
        return f"{pr_code}{seq_str}{fy}"

    # def create_view(self, project_id):

    #     project = get_object_or_404(ProjectHeader, pk=project_id)
    #     components = ProjectComponent.objects.filter(project=project)

    #     # --------------------------------------------------
    #     # BUILD COMPONENT LEVEL ROWS
    #     # --------------------------------------------------
    #     component_rows = []

    #     for comp in components:

    #         # -------- PRODUCT / SERVICE
    #         if comp.component_type in ("PRODUCT", "SERVICE"):
    #             product = comp.product or comp.service

    #             inv = Inventory.objects.filter(
    #                 product=product,
    #                 location=project.location,
    #                 sub_location=project.sub_location
    #             ).first()
                

    #             available_qty = inv.quantity if inv else 0

    #             component_rows.append({
    #                 "component": comp,
    #                 "type": comp.component_type,
    #                 "inventory": inv,
    #                 "available_qty": available_qty,
    #                 "has_stock": available_qty > 0,
    #             })

    #         # -------- BOM (COMPONENT LEVEL ONLY)
    #         elif comp.component_type == "BOM" and comp.bom:
    #             bom_items = BOMItem.objects.filter(bom=comp.bom)

    #             bom_has_stock = True
    #             bom_item_map = []

    #             for item in bom_items:
    #                 inv = Inventory.objects.filter(
    #                     product=item.product,
    #                     location=project.location,
    #                     sub_location=project.sub_location
    #                 ).first()
    #                 if not inv or inv.quantity < 0:
    #                     bom_has_stock = False

    #                 bom_item_map.append({
    #                     "item": item,
    #                     "inventory": inv,
    #                 })
                   

    #             component_rows.append({
    #                 "component": comp,
    #                 "type": "BOM",
    #                 "bom_items": bom_item_map,   # used only in POST
    #                 "has_stock": bom_has_stock,
    #             })

    #         # -------- MISC
    #         else:
    #             component_rows.append({
    #                 "component": comp,
    #                 "type": comp.component_type,
    #                 "has_stock": True,
    #             })

    #     # ==================================================
    #     # GET METHOD
    #     # ==================================================
    #     if self.request.method == "GET":
            
    #         context = {
    #                 "page_title": self.FormName,
    #                 "project": project,
    #                 "component_rows": component_rows,
    #                 "form_status": True,
    #             }

    #         context.update(self.get_extra_context())
    #         context.update(self.getTableConfig())

    #         return render(
    #             self.request,
    #             self.getTemplateName("list"),
    #             context
    #         )
        

    #     # ==================================================
    #     # POST METHOD
    #     # ==================================================
    #     else:

    #         with transaction.atomic():

    #             last_voucher = VoucherHeader.objects.order_by("-id").first()
    #             last_number = (
    #                 int(last_voucher.code.split("-")[-1])
    #                 if last_voucher else 0
    #             )

    #             voucher = VoucherHeader.objects.create(
    #                 code=f"VCH-{last_number + 1:05d}",
    #                 project=project,
    #                 voucher_status="IN_BUILD",
    #             )
    #             #goods movement header
    #             gm_date_str = date.today().strftime("%Y-%m-%d")
    #             gm_header = GoodsMovementHeader.objects.create(
    #                 code=f"GM-{voucher.code}",
    #                 project=project,
    #                 category="Issue",
    #                 voucher=voucher,
    #                 gm_date=gm_date_str,
    #                 gm_posting_date=gm_date_str,
    #             )
    #             gm_item_count = 1
    #             total_qty = 0
    #             print("component_rows:",component_rows)

    #             for row in component_rows:
    #                 comp = row["component"]
                
                    
    #                 qty = int(
    #                     self.request.POST.get(f"issue_qty_{comp.id}", 0) or 0
    #                 ) or int(
    #                             self.request.POST.get(f"bom_qty_{comp.id}", 0) or 0
    #                         )

    #                 if qty <= 0:
    #                     continue

    #                 # -------- PRODUCT / SERVICE
    #                 if row["type"] in ("PRODUCT", "SERVICE"):
    #                     inv = row["inventory"]

    #                     if not inv or inv.quantity < qty:
    #                         raise ValidationError(
    #                             f"Insufficient stock for {comp.code}"
    #                         )

    #                     VoucherComponent.objects.create(
    #                         voucherheader=voucher,
    #                         projectcomponent=comp,
    #                         inventory=inv,
    #                         voucher_qty=qty,
    #                         code=f'VC-{voucher.id:05d}-{comp.id}'
    #                     )

    #                     inv.quantity -= qty
    #                     inv.save(update_fields=["quantity"])
    #                     GoodsMovementItem.objects.create(
    #                         code=f"GMI-{gm_header.id:05d}-{gm_item_count}",
    #                         document_number=gm_header,
    #                         item_number=gm_item_count,
    #                         product=comp.product,
    #                         location=project.location,
    #                         sub_location=project.sub_location,
    #                         quantity=qty,
    #                         uom=comp.product.unit_of_measure,
    #                         gm_type="Issue",
    #                         project_component=comp,
    #                         gm_item_text=f"Issue against Voucher {voucher.code}"
    #                     )
    #                     gm_item_count += 1
    #                     total_qty += qty

    #                 # -------- BOM (VALIDATE ALL ITEMS)
    #                 elif row["type"] == "BOM":
    #                     if not row["has_stock"]:
    #                         raise ValidationError(
    #                             f"BOM stock not available for {comp.name}"
    #                         )

    #                     for bi in row["bom_items"]:
    #                         item = bi["item"]
    #                         inv = bi["inventory"]

    #                         required_qty = qty * item.bom_quantity
    #                         print("required_qty:",required_qty)

    #                         if inv.quantity < required_qty:
    #                             raise ValidationError(
    #                                 f"Insufficient stock for {item.product.name}"
    #                             )

    #                         VoucherComponent.objects.create(
    #                             voucherheader=voucher,
    #                             projectcomponent=comp,
    #                             inventory=inv,
    #                             voucher_qty=required_qty,
    #                             code=f'VC-{voucher.id:05d}-{comp.id}-{item.id}'
    #                         )

    #                         inv.quantity -= required_qty
    #                         inv.save(update_fields=["quantity"])
    #                         #print(item.product,"comp.product.unit_of_measure")
    #                         GoodsMovementItem.objects.create(
    #                         code=f"GMI-{gm_header.id:05d}-{gm_item_count}",
    #                         document_number=gm_header,
    #                         item_number=gm_item_count,
    #                         product=item.product,
    #                         location=project.location,
    #                         sub_location=project.sub_location,
    #                         quantity=qty,
    #                         uom=item.product.unit_of_measure,
    #                         gm_type="Issue",
    #                         project_component=comp,
    #                         gm_item_text=f"Issue against Voucher {voucher.code}"
    #                     )
    #                         gm_item_count += 1

    #                         total_qty += required_qty

    #                 # -------- MISC
    #                 else:
    #                     total_qty += qty
    #             print(total_qty,"totallllllllllllllll")
    #             if total_qty == 0:
    #                 voucher.delete()
    #                 messages.warning(
    #                     self.request,
    #                     "No quantity entered. Voucher not created."
    #                 )
    #                 return redirect(
    #                     "project-issue-voucher",
    #                     project_id=project.id
    #                 )

    #             voucher.voucher_qty = total_qty
    #             voucher.voucher_status = "COMPLETED"
    #             voucher.save(update_fields=["voucher_qty", "voucher_status"])

    #         messages.success(
    #             self.request,
    #             f"Issue Voucher {voucher.code} created successfully."
    #         )

    #     return redirect(
    #         "project-issue-voucher",
    #         project_id=project.id
    #     )
   
    def create_view(self, project_id):

        project = get_object_or_404(ProjectHeader, pk=project_id)
        components = ProjectComponent.objects.filter(project=project)

        component_rows = []

        # --------------------------------------------------
        # PREPARE COMPONENT DATA
        # --------------------------------------------------

        for comp in components:

            # -------- PRODUCT / SERVICE
            if comp.component_type in ("PRODUCT", "SERVICE"):
                product = comp.product or comp.service

                inv = Inventory.objects.filter(
                    product=product,
                    location=project.location,
                    sub_location=project.sub_location
                ).first()
                

                available_qty = inv.quantity if inv else 0

                component_rows.append({
                    "component": comp,
                    "type": comp.component_type,
                    "inventory": inv,
                    "available_qty": available_qty,
                    "has_stock": available_qty > 0,
                })

            # -------- BOM (COMPONENT LEVEL ONLY)
            elif comp.component_type == "BOM" and comp.bom:
                bom_items = BOMItem.objects.filter(bom=comp.bom)

                bom_has_stock = True
                bom_item_map = []

                for item in bom_items:
                    inv = Inventory.objects.filter(
                        product=item.product,
                        location=project.location,
                        sub_location=project.sub_location
                    ).first()
                    if not inv or inv.quantity < 0:
                        bom_has_stock = False

                    bom_item_map.append({
                        "item": item,
                        "inventory": inv,
                    })
                   

                component_rows.append({
                    "component": comp,
                    "type": "BOM",
                    "bom_items": bom_item_map,   # used only in POST
                    "has_stock": bom_has_stock,
                })

            # -------- MISC
            else:
                component_rows.append({
                    "component": comp,
                    "type": comp.component_type,
                    "has_stock": True,
                })

        # ==================================================
        # GET METHOD
        # ==================================================
        if self.request.method == "GET":
            
            context = {
                    "page_title": self.FormName,
                    "project": project,
                    "component_rows": component_rows,
                    "form_status": True,
                }

            context.update(self.get_extra_context())
            context.update(self.getTableConfig())

            return render(
                self.request,
                self.getTemplateName("list"),
                context
            )

        # --------------------------------------------------
        # POST
        # --------------------------------------------------

        with transaction.atomic():

            items_to_issue = []
            total_qty = 0

            # ------------------------------------------
            # COLLECT ITEMS FIRST
            # ------------------------------------------

            for row in component_rows:

                comp = row["component"]

                qty = int(
                    self.request.POST.get(f"issue_qty_{comp.id}", 0) or
                    self.request.POST.get(f"bom_qty_{comp.id}", 0) or 0
                )

                if qty <= 0:
                    continue

                # PRODUCT / SERVICE
                if row["type"] in ("PRODUCT", "SERVICE"):

                    inv = row["inventory"]

                    if not inv or inv.quantity < qty:
                        raise ValidationError(
                            f"Insufficient stock for {comp.code}"
                        )

                    items_to_issue.append({
                        "product": comp.product,
                        "inventory": inv,
                        "qty": qty,
                        "component": comp
                    })

                    total_qty += qty

                # BOM
                elif row["type"] == "BOM":

                    for bom_item in row["bom_items"]:

                        inv = Inventory.objects.filter(
                            product=bom_item.product,
                            location=project.location,
                            sub_location=project.sub_location
                        ).first()

                        required_qty = qty * bom_item.bom_quantity

                        if not inv or inv.quantity < required_qty:
                            raise ValidationError(
                                f"Insufficient stock for {bom_item.product.name}"
                            )

                        items_to_issue.append({
                            "product": bom_item.product,
                            "inventory": inv,
                            "qty": required_qty,
                            "component": comp
                        })

                        total_qty += required_qty

            # ------------------------------------------
            # NO QTY ENTERED
            # ------------------------------------------

            if total_qty == 0:

                messages.warning(
                    self.request,
                    "No quantity entered. Voucher not created."
                )

                return redirect(
                    "project-issue-voucher",
                    project_id=project.id
                )

            # ------------------------------------------
            # CREATE VOUCHER
            # ------------------------------------------

            last_voucher = VoucherHeader.objects.order_by("-id").first()

            last_number = int(last_voucher.code.split("-")[-1]) if last_voucher else 0

            voucher = VoucherHeader.objects.create(
                code=f"VCH-{last_number + 1:05d}",
                project=project,
                voucher_status="IN_BUILD",
            )

            # ------------------------------------------
            # GENERATE IVNO
            # ------------------------------------------

            pr_code = items_to_issue[0]["product"].procurementtype.Procurement_code if items_to_issue[0]["product"].procurementtype else '1'

            issue_number = self.generate_issue_voucher_number(pr_code)

            gm_date_str = date.today()

            gm_header = GoodsMovementHeader.objects.create(
                code=f"GM-{voucher.code}",
                issue_voucher_number=issue_number,
                project=project,
                category="Issue",
                voucher=voucher,
                gm_date=gm_date_str,
                gm_posting_date=gm_date_str,
            )

            # ------------------------------------------
            # CREATE ITEMS
            # ------------------------------------------

            gm_item_count = 1

            for item in items_to_issue:

                inv = item["inventory"]

                # inventory deduction
                inv.quantity -= item["qty"]
                inv.save(update_fields=["quantity"])

                # voucher component
                VoucherComponent.objects.create(
                    voucherheader=voucher,
                    projectcomponent=item["component"],
                    inventory=inv,
                    voucher_qty=item["qty"],
                    code=f"VC-{voucher.id:05d}-{item['component'].id}"
                )

                # GM item
                GoodsMovementItem.objects.create(
                    code=f"GMI-{gm_header.id:05d}-{gm_item_count}",
                    document_number=gm_header,
                    item_number=gm_item_count,
                    product=item["product"],
                    location=project.location,
                    sub_location=project.sub_location,
                    quantity=item["qty"],
                    uom=item["product"].unit_of_measure,
                    gm_type="Issue",
                    project_component=item["component"],
                    project=project,
                    gm_item_text=f"Issue against Voucher {voucher.code}"
                )

                gm_item_count += 1

            voucher.voucher_qty = total_qty
            voucher.voucher_status = "COMPLETED"
            voucher.save(update_fields=["voucher_qty", "voucher_status"])

        messages.success(
            self.request,
            f"Issue Voucher {gm_header.issue_voucher_number} created successfully."
        )

        return redirect(
            "project-issue-voucher",
            project_id=project.id
        )
 
class BaseActiveMixin:
    """
    Reusable mixin to filter ModelChoiceField querysets
    to active records (status=1 or is_active=True)
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            if isinstance(field, forms.ModelChoiceField):
                model = field.queryset.model

                if hasattr(model, 'status'):
                    field.queryset = model.objects.filter(status=1).order_by('name')
                elif hasattr(model, 'is_active'):
                    field.queryset = model.objects.filter(is_active=True).order_by('name')
                else:
                    field.queryset = model.objects.all().order_by('name')



