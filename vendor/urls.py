from django.urls import path

from . import views

urlpatterns = [

    path('vendor/list', views.VendorCRUDView.as_view(), name='vendor-list'),
    path('list', views.VendorCRUDView.as_view(), name='vendor-list'),
    path('vendor/create', views.VendorCRUDView.as_view(),  name='vendor-create'),
    path('vendor/<int:pk>/update', views.VendorCRUDView.as_view(), name='vendor-update'),
    path('vendor/<int:pk>/view', views.VendorCRUDView.as_view(), name='vendor-view'),
    path('vendor/<int:pk>/delete', views.VendorCRUDView.as_view(), name='vendor-delete'),
    
    path('vendor_type/list', views.VendorTypeCRUDView.as_view(), name='vendor_type-list'),
    path('vendor_type/create', views.VendorTypeCRUDView.as_view(),  name='vendor_type-create'),
    path('vendor_type/<int:pk>/update', views.VendorTypeCRUDView.as_view(), name='vendor_type-update'),
    path('vendor_type/<int:pk>/view', views.VendorTypeCRUDView.as_view(), name='vendor_type-view'),
    path('vendor_type/<int:pk>/delete', views.VendorTypeCRUDView.as_view(), name='vendor_type-delete'),

    path('<int:vendor_id>/vendor_bank/list', views.VendorBankCRUDView.as_view(), name='vendor-bank-list'),
    path('<int:vendor_id>/vendor_bank/create', views.VendorBankCRUDView.as_view(),  name='vendor-bank-create'),
    path('<int:vendor_id>/vendor_bank/<int:pk>/update', views.VendorBankCRUDView.as_view(), name='vendor-bank-update'),
    path('<int:vendor_id>/vendor_bank/<int:pk>/view', views.VendorBankCRUDView.as_view(), name='vendor-bank-view'),
    path('<int:vendor_id>/vendor_bank/<int:pk>/delete', views.VendorBankCRUDView.as_view(), name='vendor-bank-delete'),

    path('<int:vendor_id>/vendor_tax/list', views.VendorTaxCRUDView.as_view(), name='vendor-tax-list'),
    path('<int:vendor_id>/vendor_tax/create', views.VendorTaxCRUDView.as_view(),  name='vendor-tax-create'),
    path('<int:vendor_id>/vendor_tax/<int:pk>/update', views.VendorTaxCRUDView.as_view(), name='vendor-tax-update'),
    path('<int:vendor_id>/vendor_tax/<int:pk>/view', views.VendorTaxCRUDView.as_view(), name='vendor-tax-view'),
    path('<int:vendor_id>/vendor_tax/<int:pk>/delete', views.VendorTaxCRUDView.as_view(), name='vendor-tax-delete'),

    path('<int:vendor_id>/vendor_attachment/list', views.VendorAttachmentCRUDView.as_view(), name='vendor-attachment-list'),
    path('<int:vendor_id>/vendor_attachment/create', views.VendorAttachmentCRUDView.as_view(),  name='vendor-attachment-create'),
    path('<int:vendor_id>/vendor_attachment/<int:pk>/update', views.VendorAttachmentCRUDView.as_view(), name='vendor-attachment-update'),
    path('<int:vendor_id>/vendor_attachment/<int:pk>/view', views.VendorAttachmentCRUDView.as_view(), name='vendor-attachment-view'),
    path('<int:vendor_id>/vendor_attachment/<int:pk>/delete', views.VendorAttachmentCRUDView.as_view(), name='vendor-attachment-delete'),

    #product vendor mapping
    path('<int:product_id>/product_vendor/list', views.ProductVendorCRUDView.as_view(), name='product-vendor-list'),
    path('<int:product_id>/product_vendor/create', views.ProductVendorCRUDView.as_view(),  name='product-vendor-create'),
    path('<int:product_id>/product_vendor/<int:pk>/update', views.ProductVendorCRUDView.as_view(), name='product-vendor-update'),
    path('<int:product_id>/product_vendor/<int:pk>/view', views.ProductVendorCRUDView.as_view(), name='product-vendor-view'),
    path('<int:product_id>/product_vendor/<int:pk>/delete', views.ProductVendorCRUDView.as_view(), name='product-vendor-delete'),

    #vendor product mapping
    path('<int:vendor_id>/vendor_product/list', views.VendorProductCRUDView.as_view(), name='vendor-product-list'),
    path('<int:vendor_id>/vendor_product/create', views.VendorProductCRUDView.as_view(),  name='vendor-product-create'),
    path('<int:vendor_id>/vendor_product/<int:pk>/update', views.VendorProductCRUDView.as_view(), name='vendor-product-update'),
    path('<int:vendor_id>/vendor_product/<int:pk>/view', views.VendorProductCRUDView.as_view(), name='vendor-product-view'),
    path('<int:vendor_id>/vendor_product/<int:pk>/delete', views.VendorProductCRUDView.as_view(), name='vendor-product-delete'),

    path("vendor-search/", views.VendorSearchView.as_view(), name="vendor_search"),
    path("vendor_upload/list", views.UploadFileCRUDView.as_view(), name="vendor-upload-list"),
    path("vendor_upload/create", views.UploadFileCRUDView.as_view(), name="vendor-upload-create"),

]