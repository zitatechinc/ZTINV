from django.shortcuts import render
from django.views.generic import TemplateView
from django.db.models import Count,Sum
from vendor.models import Vendor
from catalog.models import Product
from customer.models import Customer
from inventory.models import *
import json


class MasterDashboardView(TemplateView):
    template_name = 'dashboard/master_dashboard.html'  

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # --- Vendor Data: Count Vendors by Country ---
        vendor_country_data = Vendor.objects.values('country__name').annotate(count=Count('id')).order_by('-count')
        vendor_chart_labels = [item['country__name'] or 'Unknown' for item in vendor_country_data]
        vendor_chart_data = [item['count'] for item in vendor_country_data]

        # --- Product Data: Count Products by Category ---
        category_data = Product.objects.values('category__name').annotate(count=Count('id')).order_by('-count')
        product_category_labels = [item['category__name'] or 'Uncategorized' for item in category_data]
        product_category_data = [item['count'] for item in category_data]

        # --- Product Data: Count Products by Brand ---
        brand_data = Product.objects.values('brand__name').annotate(count=Count('id')).order_by('-count')
        product_brand_labels = [item['brand__name'] or 'No Brand' for item in brand_data]
        product_brand_data = [item['count'] for item in brand_data]

        customer_data = (
        Customer.objects
        .values('customer_type')   # or country / category
        .annotate(count=Count('id')))

        customer_labels = [c['customer_type'] for c in customer_data]
        customer_counts = [c['count'] for c in customer_data]

        # --- Inventory Data ---
        total_inventory_count = Inventory.objects.count()
        total_vendors = Vendor.objects.count()
        total_products = Product.objects.count()
        total_customers = Customer.objects.count()

        # Update context with both vendor/product and inventory data
        context.update({
            'vendor_chart_labels_json': json.dumps(vendor_chart_labels),
            'vendor_chart_data_json': json.dumps(vendor_chart_data),
            'product_category_labels_json': json.dumps(product_category_labels),
            'product_category_data_json': json.dumps(product_category_data),
            'product_brand_labels_json': json.dumps(product_brand_labels),
            'product_brand_data_json': json.dumps(product_brand_data),
             'customer_chart_labels_json': json.dumps(customer_labels),
             'customer_chart_data_json': json.dumps(customer_counts),
            'total_inventory_count': total_inventory_count,
            'total_vendors': total_vendors,
            'total_products': total_products,
            'total_customers': total_customers,
        })

        return context


class VendorDashboardView(TemplateView):
    template_name = 'dashboard/vendor_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # --- Vendor Data: Count Vendors by Country ---
        vendor_country_data = Vendor.objects.values('country__name').annotate(count=Count('id')).order_by('-count')
        vendor_chart_labels = [item['country__name'] or 'Unknown' for item in vendor_country_data]
        vendor_chart_data = [item['count'] for item in vendor_country_data]

        # --- Product Data: Count Products by Category ---
        category_data = Product.objects.values('category__name').annotate(count=Count('id')).order_by('-count')
        product_category_labels = [item['category__name'] or 'Uncategorized' for item in category_data]
        product_category_data = [item['count'] for item in category_data]

        # --- Product Data: Count Products by Brand ---
        brand_data = Product.objects.values('brand__name').annotate(count=Count('id')).order_by('-count')
        product_brand_labels = [item['brand__name'] or 'No Brand' for item in brand_data]
        product_brand_data = [item['count'] for item in brand_data]

        # Pass all data as JSON to the template
        context.update({
            'vendor_chart_labels_json': json.dumps(vendor_chart_labels),
            'vendor_chart_data_json': json.dumps(vendor_chart_data),
            'product_category_labels_json': json.dumps(product_category_labels),
            'product_category_data_json': json.dumps(product_category_data),
            'product_brand_labels_json': json.dumps(product_brand_labels),
            'product_brand_data_json': json.dumps(product_brand_data),
        })

        return context
    

class InventoryDashboardView(TemplateView):
    template_name = 'dashboard/inventory_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Total Inventory Count (Number of inventory records)
        total_inventory_count = Inventory.objects.count()
        total_vendors = Vendor.objects.count()
        total_products = Product.objects.count()
        customer_count = Customer.objects.count()

        # Update context with all the data
        context.update({
            'total_inventory_count': total_inventory_count,
            'total_vendors': total_vendors,
            'total_products': total_products,
            'total_customer': customer_count,
        })

        return context
    
class SummaryDashboardView(TemplateView):
    template_name = 'dashboard/summary_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # --- Sales Activity Data ---
        sales_activity_data = {
            'to_be_packed': 228,
            'to_be_shipped': 6,
            'to_be_delivered': 10,
            'to_be_invoiced': 474
        }

        # --- Inventory Summary ---
        inventory_summary_data = {
            'quantity_in_hand': 10458,
            'quantity_to_be_received': 168
        }

        # Fetch the total count of customers, vendors, and products
        customer_count = Customer.objects.count()
        vendor_count = Vendor.objects.count()
        product_count = Product.objects.count()

        # Prepare the data for the summary dashboard
        context.update({
            'sales_activity': sales_activity_data,
            'inventory_summary': inventory_summary_data,
            'customer_count': customer_count,
            'vendor_count': vendor_count,
            'product_count': product_count,
        })

        return context