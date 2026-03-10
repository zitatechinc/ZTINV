from django.views import View
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from .forms import CategoryModelForm, ProductTypeModelForm, ProductModelForm, ProductLinksModelForm, BrandModelForm, ManufacturerModelForm, AttributesModelForm, LanguagesModelForm,ProductUploadFileModelForm,ProductGroupModelForm,ProductAttributeModelForm
from .models import Category, ProductType, Product, Brand, Manufacturer, Languages, Attribute, ProductGroup,ProductUpload, ProductAttribute
from application.models import AppSettings
from django.http import HttpResponse
from django.urls import reverse
import re, json
from core.views import BaseCRUDView, ProductBaseCRUDView,ProductFileUploadBaseCRUDView,ProductAttributesBaseView
from django.db.models import Q
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from ims.models import Units
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import traceback, time
import requests
import logging
 
logger = logging.getLogger(__name__)


class CategoryCRUDView(BaseCRUDView):
    model = Category
    form_class = CategoryModelForm
    FieldList = (('name','Name'),
                 ('parent__name','Parent'),
                 ('code','Code'),
                 ('updated_at','Updated at'),
                 ('search_keywords','Search Keywords')
                 )
    def get_extra_context(self):
        
        return {
            
        }

class BrandCRUDView(BaseCRUDView):
    model = Brand
    form_class = BrandModelForm
    FieldList = (('name','Name'),('code','Code'),('updated_at','Updated_at'), ('search_keywords','Search Keywords'))

    def get_extra_context(self):

        return {
            
        }

class ManufacturerCRUDView(BaseCRUDView):
    model = Manufacturer
    form_class = ManufacturerModelForm
    FieldList = (('name','Name'),('code','Code'),('updated_at','Updated_at'), ('search_keywords','Search Keywords'))

    def get_extra_context(self):

        return {
            
        }

class AttributesCRUDView(BaseCRUDView):
    model = Attribute
    form_class = AttributesModelForm
    FieldList = (('name','Name'),
                ('code','Code'),
                ('category__name','Category'),
                ('product_type__name','Product Type'),
                ('product_group__name','Product Group'),
                ('updated_at','Updated_at'), 
                ('search_keywords','Search Keywords'))

    def get_extra_context(self):

        return {
            
        }

class LanguagesCRUDView(BaseCRUDView):
    model = Languages
    form_class = LanguagesModelForm
    FieldList = (('name','Name'),('code','Code'),('updated_at','Updated_at'), ('search_keywords','Search Keywords'))

    def get_extra_context(self):

        return {
            
        }

class ProductTypeCRUDView(BaseCRUDView):
    model = ProductType
    form_class = ProductTypeModelForm
    FieldList = (('name','Name'),('code','Code'),('updated_at','Updated_at'), ('search_keywords','Search Keywords'))

    def get_extra_context(self):

        return {
            
        }

class ProductCRUDView(ProductBaseCRUDView):
    model = Product
    form_class = ProductModelForm

    FieldList = (('name','Name'),
                 ('category__name','Category'),
                 ('brand__name','Brand'),
                 ('product_type__name','Product Type'),
                 ('manufacturer__name','Manufacturer'),
                 ('country__name','Country'),
                 ('language__name','Language'),
                 ('unit_of_measure','Unit of Measure'),
                 ('short_description','Short Description'),
                 ('long_description','Long Description'),
                 ('updated_at','Updated at'),
                 ('search_keywords','Search Keywords')
                 )

    def globalSearchQuerySet(self, **kwargs):
        query_conditions = (Q(name__icontains=self.Keyword) | Q(search_keywords__icontains=self.Keyword)
                 | Q(code__icontains=self.Keyword)  | Q(updated_at__icontains=self.Keyword) | Q(unit_of_measure__icontains=self.Keyword)
                 | Q(category__name__icontains=self.Keyword) | Q(manufacturer__name__icontains=self.Keyword)
                 | Q(product_type__name__icontains=self.Keyword)| Q(short_description__icontains=self.Keyword)| Q(long_description__icontains=self.Keyword)
                 | Q(brand__name__icontains=self.Keyword)| Q(language__name__icontains=self.Keyword) | Q(country__name__icontains=self.Keyword
                    ))
        if kwargs:
            queryset = self.model.objects.filter(**kwargs)
            queryset = queryset.filter(query_conditions)
        else:
            queryset = self.model.objects.filter(query_conditions)
           
        return queryset
    
    def get_extra_context(self):

        return {
           
        }

class ProductUploadFileCRUDView(ProductFileUploadBaseCRUDView):
    model = ProductUpload
    form_class = ProductUploadFileModelForm
    #permission_required = [] 

    def get_extra_context(self):

        return {
            
        }

class ProductGroupCRUDView(BaseCRUDView):
    model = ProductGroup
    form_class =ProductGroupModelForm
    FieldList = (('name','Name'),('code','Code'),('updated_at','Updated_at'), ('search_keywords','Search Keywords'))

    def get_extra_context(self):

        return {
            
        }        

class ProductSearchView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        q = request.GET.get("q", "").strip()
        results = []

        if q:
            vendors = (
                Product.objects.filter(Q(name__icontains=q), status=1)
                .values("id", "name")[:10]
            )
            results = [
                {"id": v["id"], "text": v["name"]}
                for v in vendors
            ]

        return JsonResponse({"results": results})

class ProductAttributesCRUDView(ProductAttributesBaseView):
    model = ProductAttribute
    form_class = ProductAttributeModelForm
    FieldList = (('name','Name'),('code','Code'),('updated_at','Updated_at'), ('search_keywords','Search Keywords'))

    def get_extra_context(self):

        return {
            
        }    
    
from django.http import JsonResponse
from django.views import View
from django.apps import apps

# class GenericFKCreateView(View):

#     def post(self, request, *args, **kwargs):
#         app_label = request.POST.get("app_label")
#         model_name = request.POST.get("model")
#         name = request.POST.get("name")

#         if not app_label or not model_name or not name:
#             return JsonResponse({"error": "Invalid request"}, status=400)

#         model = apps.get_model(app_label, model_name)

#         obj = model.objects.create(name=name)

#         return JsonResponse({
#             "id": obj.pk,
#             "text": str(obj)
#         })

# core/views/ajax_fk.py

# class GenericFKCreateView(View):

#     def post(self, request, *args, **kwargs):
#         app_label = request.POST.get("app_label")
#         model_name = request.POST.get("model")
#         name = request.POST.get("name")

#         if not app_label or not model_name or not name:
#             return JsonResponse({"error": "Invalid request"}, status=400)

#         model = apps.get_model(app_label, model_name)

#         # ✅ Dynamic permission check
#         perm = f"{app_label}.add_{model_name.lower()}"
#         if not request.user.has_perm(perm):
#             return JsonResponse({"error": "Permission denied"}, status=403)

#         # Prevent duplicates
#         obj, created = model.objects.get_or_create(name=name.strip())

#         return JsonResponse({
#             "id": obj.pk,
#             "text": str(obj)
#         })


import logging
logger = logging.getLogger(__name__)


class GenericFKCreateView(View):

    def get(self, request, *args, **kwargs):

        """Return existing objects for Select2 AJAX dropdown."""
        app_label = request.GET.get("app_label")
        model_name = request.GET.get("model")
        query_text = request.GET.get("q")

        logger.info(f"AJAX GET called for app: {app_label}, model: {model_name}")

        if not app_label or not model_name:
            logger.warning("Missing app_label or model_name in GET request")
            return JsonResponse({"results": []})
        try:
            model = apps.get_model(app_label, model_name)
            
        except LookupError:
            logger.error(f"Model not found: {app_label}.{model_name}")
            return JsonResponse({"results": []})
        objects = model.objects.filter(status=1) if hasattr(model, 'status') else model.objects.all()
        if query_text:
            objects = objects.filter(name__icontains=query_text)
            
        data = [{"id": obj.pk, "text": str(obj)} for obj in objects]

        logger.info(f"Returning {len(data)} items for {model_name}")
        return JsonResponse({"results": data})

    def post(self, request, *args, **kwargs):
        """Create a new object for Select2 AJAX 'tags'."""
        app_label = request.POST.get("app_label")
        model_name = request.POST.get("model")
        name = request.POST.get("name")

        logger.info(f"AJAX POST called: app={app_label}, model={model_name}, name={name}, user={request.user}")

        if not app_label or not model_name or not name:
            logger.error("Invalid request data in POST")
            return JsonResponse({"error": "Invalid request"}, status=400)

        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            logger.error(f"Model not found: {app_label}.{model_name}")
            return JsonResponse({"error": "Model not found"}, status=400)

        perm = f"{app_label}.add_{model_name.lower()}"
        logger.info(f"Checking permission: {perm}")

        if not request.user.has_perm(perm):
            logger.warning(f"Permission denied for user {request.user}")
            return JsonResponse({"error": "Permission denied"}, status=403)

        obj, created = model.objects.get_or_create(name=name.strip())
        logger.info(f"Object {'created' if created else 'exists'}: ID={obj.pk}, Name={obj.name}")

        return JsonResponse({"id": obj.pk, "text": str(obj)})

@api_view(['GET'])
def uom_list(request):
    logger.info("uom_list API called")
    try:
        units = Units.objects.all()
        logger.debug(f"Total projects fetched: {units.count()}")  

        data = []
        for i in units:
            data.append({
                "id": i.id,
                "name" : i.unit
            })

        logger.info("uom_list API executed successfully")
        return Response({"data": data})

    except Exception as e:
        logger.exception("Error occurred in uom_list API")
        return Response(
            {"message": "Something went wrong while fetching units"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
