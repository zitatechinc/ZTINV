from django.urls import path

from . import views

urlpatterns = [

    path('customer/list', views.CustomerCRUDView.as_view(), name='customer-list'),
    path('customer/create', views.CustomerCRUDView.as_view(),  name='customer-create'),
    path('customer/<int:pk>/update', views.CustomerCRUDView.as_view(), name='customer-update'),
        path('customer/<int:pk>/view', views.CustomerCRUDView.as_view(), name='customer-view'),
    path('customer/<int:pk>/delete', views.CustomerCRUDView.as_view(), name='customer-delete'),
    
]