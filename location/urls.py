from django.urls import path

from .import views

urlpatterns = [
    path('country/list', views.CountryCRUDView.as_view(), name='country-list'),
    path('country/create', views.CountryCRUDView.as_view(),  name='country-create'),
    path('country/<int:pk>/update', views.CountryCRUDView.as_view(), name='country-update'),
    path('country/<int:pk>/delete', views.CountryCRUDView.as_view(), name='country-delete'),
    path('country/<int:pk>/view', views.CountryCRUDView.as_view(), name='country-view'),

    path('location/list', views.LocationCRUDView.as_view(), name='location-list'),
    path('location/create', views.LocationCRUDView.as_view(),  name='location-create'),
    path('location/<int:pk>/update', views.LocationCRUDView.as_view(), name='location-update'),
    path('location/<int:pk>/delete', views.LocationCRUDView.as_view(), name='location-delete'),
    path('location/<int:pk>/view', views.LocationCRUDView.as_view(), name='location-view'),

    path('sub_location/list', views.SubLocationCRUDView.as_view(), name='sub-location-list'),
    path('sub_location/create', views.SubLocationCRUDView.as_view(),  name='sub-location-create'),
    path('sub_location/<int:pk>/update', views.SubLocationCRUDView.as_view(), name='sub-location-update'),
    path('sub_location/<int:pk>/delete', views.SubLocationCRUDView.as_view(), name='sub-location-delete'),
    path('sub_location/<int:pk>/view', views.SubLocationCRUDView.as_view(), name='sub-location-view'),

    # AJAX URLs to load states and sublocations
    #path('ajax/get-countries/', views.get_countries, name='country-list'),
    path('ajax/get-states/', views.get_states, name='ajax_get_states'),
    path('ajax/get-sublocations/', views.get_sublocations, name='ajax_get_sublocations'),

]