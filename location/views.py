from django.views import View
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from .forms import CountryModelForm,LocationModelForm,SubLocationModelForm
from .models import Country,Location,SubLocation
from application.models import AppSettings
from django.http import HttpResponse
from django.urls import reverse
import re
from core.views import BaseCRUDView
from django.db.models import Q
from django.contrib.auth.mixins import PermissionRequiredMixin


class CountryCRUDView(BaseCRUDView):
    model = Country
    form_class = CountryModelForm
    FieldList = (('name','Name'),
                 ('code','Code'),
                 ('updated_at','Updated at'),
                 ('search_keywords','Search Keywords')
                 )
    def get_extra_context(self):
        
        return {
            
        }
    
class LocationCRUDView(BaseCRUDView):
    model = Location
    form_class = LocationModelForm
    FieldList = (('name','Name'),
                 ('code','Code'),
                 ('region','Region'),
                 ('city','City'),
                 ('updated_at','Updated at'),
                 ('search_keywords','Search Keywords')
                 )
    def get_extra_context(self):
        
        return {
            
        }
    
class SubLocationCRUDView(BaseCRUDView):
    model = SubLocation
    form_class = SubLocationModelForm
    FieldList = (
        ('name', 'Name'),
        ('code', 'Code'),
        ('location__name', 'Location'),
        ('updated_at', 'Updated at'),
        ('search_keywords', 'Search Keywords')
    )

    def get_extra_context(self):
        
        return {
            
        }

# location/views.py
from django.http import JsonResponse

def get_countries(request):
    countries = Country.objects.filter(status=1).values('id', 'name')  
    return JsonResponse({'countries': list(countries)})

def get_states(request):
    country_id = request.GET.get('country_id')
    if country_id:
        states = Location.objects.filter(country_id=country_id, status=1).values('id', 'name')
        states_list = list(states)
    else:
        states_list = []
    return JsonResponse({'states': states_list})

def get_sublocations(request):
    state_id = request.GET.get('state_id')
    if state_id:
        sublocations = SubLocation.objects.filter(location_id=state_id, status=1).values('id', 'name')
        sublocations_list = list(sublocations)
    else:
        sublocations_list = []
    return JsonResponse({'sublocations': sublocations_list})