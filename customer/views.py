from django.views import View
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from .forms import CustomerModelForm
from .models import Customer
from django.utils import timezone
from django.db import transaction
from application.models import AppSettings
from django.http import HttpResponse
from django.urls import reverse
import re
from core.views import BaseCRUDView
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
import traceback
# views.py
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from decimal import Decimal
from django.core.exceptions import ValidationError

class CustomerCRUDView(BaseCRUDView):
    model = Customer
    form_class = CustomerModelForm

    FieldList = (('company_name1','Company Name1'),
                ('customer_type','Customer Type'),
                 ('country__name','Country'),
                 ('zipcode','Zipcode'),
                 ('payment_terms','Payment Terms'),
                 ('updated_at','Updated at'),
                 ('search_keywords','Search Keywords')
                 )

    def get_extra_context(self):
        
        return {
            
        }   

