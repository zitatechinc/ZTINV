from django.urls import path

from application import views


urlpatterns = [
    path('themes/list', views.ThemesCRUDView.as_view(), name='theme-list'),
    path('themes/create', views.ThemesCRUDView.as_view(),  name='theme-create'),
    path('themes/<int:pk>/update', views.ThemesCRUDView.as_view(), name='theme-update'),
    path('themes/<int:pk>/delete', views.ThemesCRUDView.as_view(), name='theme-delete'),
    
    path('app_settings/list', views.AppSettingsCRUDView.as_view(), name='app-list'),
    path('app_settings/create', views.AppSettingsCRUDView.as_view(), name='app-create'),
    path('app_settings/<int:pk>/update', views.AppSettingsCRUDView.as_view(), name='app-update'),
    path('app_settings/<int:pk>/view', views.AppSettingsCRUDView.as_view(), name='app-view'),
    path('app_settings/<int:pk>/delete', views.AppSettingsCRUDView.as_view(), name='app-delete'),

    path('log_entry/list', views.AuditLogCRUDView.as_view(), name='logentry-list'),

    path('bom_log_entry/list', views.BOMAuditLogCRUDView.as_view(), name='bom-logentry-list'),
]