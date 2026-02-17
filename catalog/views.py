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