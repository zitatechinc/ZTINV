from django.urls import path
from django.conf.urls import handler404, handler500
from django.shortcuts import render
from . import views

urlpatterns = [
    path('purchase_order/create', views.create_po, name='create_po'),
    path('purchase_order_type/list', views.PurchaseOrderTypeCRUDView.as_view(), name='purchase_order_type-list'),
    path('purchase_order_type/create', views.PurchaseOrderTypeCRUDView.as_view(),  name='purchase_order_type-create'),
    path('purchase_order_type/<int:pk>/update', views.PurchaseOrderTypeCRUDView.as_view(), name='purchase_order_type-update'),
    path('purchase_order_type/<int:pk>/view', views.PurchaseOrderTypeCRUDView.as_view(), name='purchase_order_type-view'),
    path('purchase_order_type/<int:pk>/delete', views.PurchaseOrderTypeCRUDView.as_view(), name='purchase_order_type-delete'),
 
    path('purchase_order_status/list', views.PurchaseOrderStatusCRUDView.as_view(), name='purchase_order_status-list'),
    path('purchase_order_status/create', views.PurchaseOrderStatusCRUDView.as_view(),  name='purchase_order_status-create'),
    path('purchase_order_status/<int:pk>/update', views.PurchaseOrderStatusCRUDView.as_view(), name='purchase_order_status-update'),
    path('purchase_order_status/<int:pk>/view', views.PurchaseOrderStatusCRUDView.as_view(), name='purchase_order_status-view'),
    path('purchase_order_status/<int:pk>/delete', views.PurchaseOrderStatusCRUDView.as_view(), name='purchase_order_status-delete'),

    path('goods_receiver/list', views.GoodsReceiverCrudView.as_view(), name='goods-receiver-list'),
    path('goods_receiver/create', views.GoodsReceiverCrudView.as_view(),  name='goods-receiver-create'),
    path('goods_receiver/create/<int:pk>', views.GoodsReceiverCrudView.as_view(),  name='goods-receiver-view-create'),
    path('goods_receiver/<int:pk>/update', views.GoodsReceiverCrudView.as_view(), name='goods-receiver-update'),
    path('goods_receiver/<int:pk>/delete', views.GoodsReceiverCrudView.as_view(), name='goods-receiver-delete'),

    path('quality_management/list', views.QualityManagementCrudView.as_view(), name='quality-management-list'),
    path('quality_management/create', views.QualityManagementCrudView.as_view(),  name='quality-management-create'),
    path('quality_management/create/<int:pk>', views.QualityManagementCrudView.as_view(),  name='quality-management-view-create'),
    path('quality_management/<int:pk>/update', views.QualityManagementCrudView.as_view(), name='quality-management-update'),
    path('quality_management/<int:pk>/delete', views.QualityManagementCrudView.as_view(), name='quality-management-delete'),

    path('inventory_search/list', views.InventorySearchCrudView.as_view(), name='inventory-search-list'),
    path('inventory_search/create', views.InventorySearchCrudView.as_view(),  name='inventory-search-create'),

    path('<int:vendor_id>/purchase_order_header/list', views.PurchaseOrderHeaderCRUDView.as_view(), name='purchase_order_header-list'),
    path('<int:vendor_id>/purchase_order_header/create', views.PurchaseOrderHeaderCRUDView.as_view(),  name='purchase_order_header-create'),
    path('<int:vendor_id>/purchase_order_header/<int:pk>/update', views.PurchaseOrderHeaderCRUDView.as_view(), name='purchase_order_header-update'),
    path('<int:vendor_id>/purchase_order_header/<int:pk>/view', views.PurchaseOrderHeaderCRUDView.as_view(), name='purchase_order_header-view'),
    path('<int:vendor_id>/purchase_order_header/<int:pk>/delete', views.PurchaseOrderHeaderCRUDView.as_view(), name='purchase_order_header-delete'),

    path('<int:po_id>/bulk_goods_receipt/update', views.bulk_goods_receipt, name='bulk_goods_receipt'),
    path('<int:po_id>/quality_management_receipt/update', views.quality_management_receipt, name='quality_management_receipt'),
    path('<int:po_id>/purchase_order_item/list', views.PurchaseOrderItemsCRUDView.as_view(), name='purchase_order_item-list'),
    path('<int:po_id>/purchase_order_item/create', views.PurchaseOrderItemsCRUDView.as_view(),  name='purchase_order_item-create'),
    path('<int:po_id>/purchase_order_item/<int:pk>/update', views.PurchaseOrderItemsCRUDView.as_view(), name='purchase_order_item-update'),
    path('<int:po_id>/purchase_order_item/<int:pk>/view', views.PurchaseOrderItemsCRUDView.as_view(), name='purchase_order_item-view'),
    path('<int:po_id>/purchase_order_item/<int:pk>/delete', views.PurchaseOrderItemsCRUDView.as_view(), name='purchase_order_item-delete'),

    path('inventory/gm-history/', views.inventory_gm_history, name='inventory-gm-history'),
    path('inventory/serial-numbers/', views.inventory_serial_numbers, name='inventory-serial-numbers'),

    path("po_list", views.PO_list, name="po_list"),

    # Regular view for displaying the inspection receipt form/page
    path('inspection/receipt/', views.inspection_receipt_view, name='inspection_receipt'),

    # PDF generation view
    path("quality-management-pdf/<int:pk>/<str:prv_number>/<str:report_type>/", views.quality_management_pdf, name='quality-management-pdf'),

    path("purchase-order-list/<int:pk>", views.purchase_order_list, name='purchase-order-list'),

    #po report
    path('po_report/create', views.POReportCrudView.as_view(),  name='po_report_create'),
    path('voucher/pdf/', views.download_voucher_pdf, name="download_voucher_pdf")

]

