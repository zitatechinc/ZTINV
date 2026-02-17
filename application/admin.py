from django.contrib import admin
from django.contrib.auth.models import Group
from accounts.models import User
# from store.models import StoreInformation, MaterialType, MaterialGroup,UnitMeasure,MaterialStatus

# Register your models here.

admin.site.site_header = 'ZitaTech Inventory App (Administration)'
admin.site.site_title = 'ZitaTech Inventory Application'
admin.site.index_title = 'ZitaTech Inventory Application'

# class UserAdmin(admin.ModelAdmin):
#     listperpage = 10
#     list_display = ('id', 'first_name', 'last_name')


# class MaterialTypeAdmin(admin.ModelAdmin):
#     listperpage = 10
#     list_display = ('id', 'name', 'code', 'created_at', 'updated_at', 'created_user', 'updated_user')

# class MaterialGroupAdmin(admin.ModelAdmin):
#     listperpage = 10
#     list_display = ('id', 'name', 'code', 'created_at', 'updated_at', 'created_user', 'updated_user')

# class UnitMeasureAdmin(admin.ModelAdmin):
#     listperpage = 10
#     list_display = ('id', 'name', 'code', 'created_at', 'updated_at', 'created_user', 'updated_user')

# class MaterialStatusAdmin(admin.ModelAdmin):
#     listperpage = 10
#     list_display = ('id', 'name', 'code', 'created_at', 'updated_at', 'created_user', 'updated_user')

# class StoreInformationAdmin(admin.ModelAdmin):
#     listperpage = 10
#     list_display = ('id', 'name', 'code', 'created_at', 'updated_at', 'created_user', 'updated_user')
    

# admin.site.unregister(Group)
# admin.site.register(User, UserAdmin)
# admin.site.register(StoreInformation, StoreInformationAdmin)
# admin.site.register(MaterialType, MaterialTypeAdmin)
# admin.site.register(MaterialGroup,MaterialGroupAdmin)
# admin.site.register(UnitMeasure, UnitMeasureAdmin)
# admin.site.register(MaterialStatus, MaterialStatusAdmin)


