# dashboard/urls.py

from django.urls import path
from .views import MasterDashboardView,SummaryDashboardView,InventoryDashboardView,VendorDashboardView  # Import the class-based view

urlpatterns = [
    path('dashboard/', MasterDashboardView.as_view(), name='master_dashboard'),
    path('vendor_dashboard/', VendorDashboardView.as_view(), name='vendor_dashboard'),
    path('inventory_dashboard/', InventoryDashboardView.as_view(), name='inventory_dashboard'),
    
]
