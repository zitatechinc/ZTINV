from django.views import View
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from .forms import VendorModelForm, VendorTypeModelForm, VendorBankModelForm,VendorTaxModelForm, VendorAttachmentModelForm,ProductVendorModelForm,UploadFileModelForm,VendorProductModelForm
from .models import Vendor, VendorType, VendorBank, VendorTax, VendorAttachment,ProductVendor,VendorUpload
from django.utils import timezone
from django.db import transaction
from application.models import AppSettings
from django.http import HttpResponse
from django.urls import reverse
import re
from core.views import BaseCRUDView, VendorBaseCRUDView, ProductVendorBaseCRUDView,FileUploadBaseCRUDView, VendorProductBaseCRUDView
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
import traceback
# views.py
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from decimal import Decimal
from django.core.exceptions import ValidationError


@login_required
def vendor_search(request):
    results = []
    q = request.GET.get('q', '')
    try:
        vendors = Vendor.objects.filter(company_name1__icontains=q, status=1)[:10]  # limit results
        for v in vendors:
            results.append({
                "id": v.id,
                "text": f"{v.company_name1}",  
            })
    except Exception as e:
        print (e)

    return JsonResponse({"results": results})


class VendorSearchView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        q = request.GET.get("q", "").strip()
        results = []

        if q:
            vendors = (
                Vendor.objects.filter(Q(company_name1__icontains=q), status=1)
                .values("id", "company_name1")[:10]
            )
            results = [
                {"id": v["id"], "text": v["company_name1"]}
                for v in vendors
            ]

        return JsonResponse({"results": results})




class VendorCRUDView(BaseCRUDView):
    model = Vendor
    form_class = VendorModelForm

    FieldList = (('company_name1','Company Name1'),
                ('vendor_type','Vendor Type'),
                 ('country__name','Country'),
                 ('zipcode','Zipcode'),
                 ('payment_terms','Payment Terms'),
                 ('updated_at','Updated at'),
                 ('search_keywords','Search Keywords')
                 )

    def get_extra_context(self):
        
        return {
            
        }   

class VendorTypeCRUDView(BaseCRUDView):
    model = VendorType
    form_class = VendorTypeModelForm
    FieldList = (('name','Name'),('code','Code'),('updated_at','Updated_at'), ('search_keywords','Search Keywords'))

    

    def get_extra_context(self):

        return {
            
        }


class VendorTaxCRUDView(VendorBaseCRUDView):
    model = VendorTax
    form_class = VendorTaxModelForm
    

    def get_extra_context(self):

        return {
            
        }        

class VendorBankCRUDView(VendorBaseCRUDView):
    model = VendorBank
    form_class = VendorBankModelForm
    

    def get_extra_context(self):

        return {
            
        }

class VendorAttachmentCRUDView(VendorBaseCRUDView):
    model = VendorAttachment
    form_class = VendorAttachmentModelForm
    

    def get_extra_context(self):

        return {
            
        }

class ProductVendorCRUDView(ProductVendorBaseCRUDView):
    model = ProductVendor
    form_class = ProductVendorModelForm
    #permission_required = [] 

    def get_extra_context(self):

        return {
            
        }
    
class VendorProductCRUDView(VendorProductBaseCRUDView):
    model = ProductVendor
    form_class = VendorProductModelForm
    #permission_required = [] 

    def get_extra_context(self):

        return {
            
        }        

class UploadFileCRUDView(FileUploadBaseCRUDView):
    model = VendorUpload
    form_class = UploadFileModelForm
    #permission_required = [] 

    def get_extra_context(self):

        return {
            
        }