from django.core.management.base import BaseCommand
from catalog.models import (
    Manufacturer, Languages, Brand, ProductType, Category, Product, ProductLinks, ProductGroup
)
from vendor.models import PurchaseOrderHeader, PurchaseOrderItem
from accounts.models import User
from location.models import Location, SubLocation
import random
from location.models import Country
from datetime import datetime
from accounts.models import User
import pandas as pd 
from datetime import datetime
import random



class Command(BaseCommand):

    help = "Insert GM Items  using update_or_create"
    def handle(self, *args, **kwargs):

        try:
            sub_loc = random.choice(SubLocation.objects.all())
            location = sub_loc.location
            created_user_obj =  User.objects.filter(pk=1).first()
            modifled_user_obj =  User.objects.filter(pk=1).first()
            print (created_user_obj, modifled_user_obj, PurchaseOrderItem.objects.all().count())
            for each in PurchaseOrderItem.objects.all():
            
                    each.created_user=created_user_obj
                    each.updated_user=modifled_user_obj
                    each.po_location=location
                    each.sub_location=sub_loc
                    each.save()

                    
            PurchaseOrderHeader.objects.all().update(
                created_user=created_user_obj,
                    updated_user=modifled_user_obj

                )
            #print("master references are not there")
        except Exception as e:
            print(str(e))
