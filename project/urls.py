from django.urls import path
from django.conf.urls import handler404, handler500
from django.shortcuts import render

from . import views

urlpatterns = [
    
    path('project_search/create', views.ProjectSearchView.as_view(),  name='project-search-create'),
    path('<int:po_id>/project_header_receipt/update', views.project_header_receipt, name='project_header_receipt'),

    path("projects_list", views.project_list, name="project_list"),

    # ProjectHeader
    path('project_header/list', views.ProjectHeaderCrudView.as_view(), name='project-header-list'),
    path('project_header/create', views.ProjectHeaderCrudView.as_view(), name='project-header-create'),
    path('project_header/<int:pk>/update', views.ProjectHeaderCrudView.as_view(), name='project-header-update'),
    path('project_header/<int:pk>/view', views.ProjectHeaderCrudView.as_view(), name='project-header-view'),
    path('project_header/<int:pk>/delete', views.ProjectHeaderCrudView.as_view(), name='project-header-delete'),
    path('project_header/<int:pk>/history', views.ProjectHeaderCrudView.as_view(), name='project-audit'),
    

    path('project_header/<int:pk>/view', views.ProjectHeaderCrudView.as_view(), name='project-header-view'),


     # ProjectComponent

    path('project_header/<int:pk>/view', views.ProjectHeaderCrudView.as_view(), name='project-header-view'),
    path("<int:project_id>/voucher_header/create",  views.ProjectIssueVoucherBaseView.as_view(),    name="project-issue-voucher"),

     # ProjectComponent

    path('<int:project_id>/project_component/list', views.ProjectComponentCrudView.as_view(), name='project-component-list'),
    path('<int:project_id>/project_component/create', views.ProjectComponentCrudView.as_view(), name='project-component-create'),
    path('<int:project_id>/project_component/<int:pk>/view', views.ProjectComponentCrudView.as_view(), name='project-component-view'),
    path('<int:project_id>/project_component/<int:pk>/update', views.ProjectComponentCrudView.as_view(), name='project-component-update'),
    path('<int:project_id>/project_component/<int:pk>/delete', views.ProjectComponentCrudView.as_view(), name='project-component-delete'),
    path('<int:project_id>/project_component/<int:pk>/history', views.ProjectComponentCrudView.as_view(), name='project-component-audit'),

    #search
    path('bom/create', views.BOMSearchView.as_view(),  name='bom-create'),
    path('<int:po_id>/bom_header_receipt/update', views.bom_header_receipt, name='bom_header_receipt'),


    # BOMHeader
    path('bom_header/list', views.BOMHeaderCrudView.as_view(), name='bom-header-list'),
    path('bom_header/create', views.BOMHeaderCrudView.as_view(), name='bom-header-create'),
    path('bom_header/<int:pk>/view', views.BOMHeaderCrudView.as_view(), name='bom-header-view'),
    path('bom_header/<int:pk>/update', views.BOMHeaderCrudView.as_view(), name='bom-header-update'),
    path('bom_header/<int:pk>/delete', views.BOMHeaderCrudView.as_view(), name='bom-header-delete'),

    # BOMItem
    path('<int:bom_id>/b_o_m_item/list', views.BOMItemCrudView.as_view(), name='bom-item-list'),
    path('<int:bom_id>/b_o_m_item/create', views.BOMItemCrudView.as_view(), name='bom-item-create'),
    path('<int:bom_id>/b_o_m_item/<int:pk>/view', views.BOMItemCrudView.as_view(), name='bom-item-view'),
    path('<int:bom_id>/b_o_m_item/<int:pk>/update', views.BOMItemCrudView.as_view(), name='bom-item-update'),
    path('<int:bom_id>/b_o_m_item/<int:pk>/delete', views.BOMItemCrudView.as_view(), name='bom-item-delete'),

    path('<int:bom_id>/b_o_m_attachments/list/', views.BOMAttachmentsCrudView.as_view(), name='bom-attachment-list'),
    path('<int:bom_id>/b_o_m_attachments/create/', views.BOMAttachmentsCrudView.as_view(), name='bom-attachment-create'),
    path('<int:bom_id>/b_o_m_attachments/<int:pk>/view/', views.BOMAttachmentsCrudView.as_view(), name='bom-attachment-view'),
    path('<int:bom_id>/b_o_m_attachments/<int:pk>/update/', views.BOMAttachmentsCrudView.as_view(), name='bom-attachment-update'),
    path('<int:bom_id>/b_o_m_attachments/<int:pk>/delete/', views.BOMAttachmentsCrudView.as_view(), name='bom-attachment-delete'),
    path('<int:bom_id>/b_o_m_attachments/<int:pk>/download/', views.download_attachment, name='bom-attachment-download'),


    #voucher
    path('voucher_search/create', views.VoucherSearchView.as_view(),  name='voucher-search-create'),
    #path('<int:project_id>/voucher_search/create', views.VoucherSearchView.as_view(),  name='voucher-search-create'),



    path('<int:po_id>/voucher_header_receipt/update', views.voucher_header_receipt, name='voucher_header_receipt'),

    path('<int:po_id>/issue_voucher_edit_receipt/update', views.issue_voucher_edit_receipt, name='issue_voucher_edit_receipt'),


]

