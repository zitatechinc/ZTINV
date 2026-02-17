from django.urls import path

from . import views

urlpatterns = [
    path('category/list', views.CategoryCRUDView.as_view(), name='category-list'),
    path('category/create', views.CategoryCRUDView.as_view(),  name='category-create'),
    path('category/<int:pk>/update', views.CategoryCRUDView.as_view(), name='category-update'),
    path('category/<int:pk>/view', views.CategoryCRUDView.as_view(), name='category-view'),
    path('category/<int:pk>/delete', views.CategoryCRUDView.as_view(), name='category-delete'),
    
    path('product_type/list', views.ProductTypeCRUDView.as_view(), name='product_type-list'),
    path('product_type/create', views.ProductTypeCRUDView.as_view(),  name='product_type-create'),
    path('product_type/<int:pk>/update', views.ProductTypeCRUDView.as_view(), name='product_type-update'),
    path('product_type/<int:pk>/view', views.ProductTypeCRUDView.as_view(), name='product_type-view'),
    path('product_type/<int:pk>/delete', views.ProductTypeCRUDView.as_view(), name='product_type-delete'),
    
    path('brand/list', views.BrandCRUDView.as_view(), name='brand-list'),
    path('brand/create', views.BrandCRUDView.as_view(),  name='brand-create'),
    path('brand/<int:pk>/update', views.BrandCRUDView.as_view(), name='brand-update'),
    path('brand/<int:pk>/view', views.BrandCRUDView.as_view(), name='brand-view'),
    path('brand/<int:pk>/delete', views.BrandCRUDView.as_view(), name='brand-delete'),
    path('brand/<int:pk>/history', views.BrandCRUDView.as_view(), name='brand-audit'),
    
    path('manufacturer/list', views.ManufacturerCRUDView.as_view(), name='manufacturer-list'),
    path('manufacturer/create', views.ManufacturerCRUDView.as_view(),  name='manufacturer-create'),
    path('manufacturer/<int:pk>/update', views.ManufacturerCRUDView.as_view(), name='manufacturer-update'),
    path('manufacturer/<int:pk>/view', views.ManufacturerCRUDView.as_view(), name='manufacturer-view'),
    path('manufacturer/<int:pk>/delete', views.ManufacturerCRUDView.as_view(), name='manufacturer-delete'),
    
    path('attribute/list', views.AttributesCRUDView.as_view(), name='attribute-list'),
    path('attribute/create', views.AttributesCRUDView.as_view(),  name='attribute-create'),
    path('attribute/<int:pk>/update', views.AttributesCRUDView.as_view(), name='attribute-update'),
    path('attribute/<int:pk>/view', views.AttributesCRUDView.as_view(), name='attribute-view'),
    path('attribute/<int:pk>/delete', views.AttributesCRUDView.as_view(), name='attribute-delete'),

    path('languages/list', views.LanguagesCRUDView.as_view(), name='languages-list'),
    path('languages/create', views.LanguagesCRUDView.as_view(),  name='languages-create'),
    path('languages/<int:pk>/update', views.LanguagesCRUDView.as_view(), name='languages-update'),
    path('languages/<int:pk>/view', views.LanguagesCRUDView.as_view(), name='languages-view'),
    path('languages/<int:pk>/delete', views.LanguagesCRUDView.as_view(), name='languages-delete'),

    path('product/list', views.ProductCRUDView.as_view(), name='product-list'),
    path('product/create', views.ProductCRUDView.as_view(),  name='product-create'),
    path('product/<int:pk>/update', views.ProductCRUDView.as_view(), name='product-update'),
    path('product/<int:pk>/view', views.ProductCRUDView.as_view(), name='product-view'),
    path('product/<int:pk>/delete', views.ProductCRUDView.as_view(), name='product-delete'),
    
    #ProductAttributes
    path('<int:product_id>/product_attribute/create', views.ProductAttributesCRUDView.as_view(), name='product-attribute-create'),
    path('<int:product_id>/product_attribute/update', views.ProductAttributesCRUDView.as_view(), name='product-attribute-update'),
    path('<int:product_id>/product_attribute/delete', views.ProductAttributesCRUDView.as_view(), name='product-attribute-delete'),
    path('<int:product_id>/product_attribute/view', views.ProductAttributesCRUDView.as_view(), name='product-attribute-view'),
    path('<int:product_id>/product_attribute/list', views.ProductAttributesCRUDView.as_view(), name='product-attribute-list'),

    path("product_upload/list", views.ProductUploadFileCRUDView.as_view(), name="product-upload-list"),
    path("product_upload/create", views.ProductUploadFileCRUDView.as_view(), name="product-upload-create"),

    path('product_group/list', views.ProductGroupCRUDView.as_view(), name='product-group-list'),
    path('product_group/create', views.ProductGroupCRUDView.as_view(),  name='product-group-create'),
    path('product_group/<int:pk>/update', views.ProductGroupCRUDView.as_view(), name='product-group-update'),
    path('product_group/<int:pk>/view', views.ProductGroupCRUDView.as_view(), name='product-group-view'),
    path('product_group/<int:pk>/delete', views.ProductGroupCRUDView.as_view(), name='product-group-delete'),

    path("product-search/", views.ProductSearchView.as_view(), name="product_search"),
]