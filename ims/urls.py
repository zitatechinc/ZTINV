"""IMS_NEW URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from ims.views import *
from django.conf import settings
from django.views.static import serve  
from django.conf.urls.static import static
from ims import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', Login.as_view(), name='login'),  #Login.html
    
    path('register_user/', RegisterUserView.as_view(), name='register_user'),
    path('invoice_page/', InvoicePageView.as_view(), name='invoice_page'),
    path('po_data/', PODataView.as_view(), name='po_data'),
    path('user_profile/', ProfileView.as_view(), name='user_profile'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),# Custom logout view
    path('forgot_password/', ForgotPasswordView.as_view(), name='forgot_password'),# Forgot password view
    path('procurement/', ProcurementView.as_view(), name='procurement'),# Procurement view
    path('procurement/save_draft/', views.draft_procurement, name='procurement_draft'),# Save draft procurement
    path('RA/', RAProcurementView.as_view(), name='ra_procurement'),# RA Procurement view
    path('project-create/', ProjectCreateView.as_view(), name='project-create'),# Project creation view
    path('po-create/', POCreateView.as_view(), name='po-create'),
    path('vender-create/',VendorCreateView.as_view(),name='vender-create'),# Vendor creation view
    path('imm/', ProcurementIMMView.as_view(), name='imm'),# IMM procurement view
    path('rejectedimm/', RejectedimmView.as_view(),name="rejectedimm"),# Rejected IMM view
    path('retunedpr/',ReturnRaView.as_view(),name="retunedpr"),# Returned PR view
    path('budget/', BudgetAllocationView.as_view(), name='budget_allocation_view'),# Budget allocation view
    path('budget-logs/<str:project_id>/', BudgetLogsAPI.as_view(), name='budget_logs_api'),# Budget logs API
    path('accounts/',AccountView.as_view(),name="accounts"),# Accounts view
    path('AApr/',ApproveAuthorityView.as_view(),name="aapr"),# Approve Authority view
    path('submittedpr/', SubmittedPr.as_view(), name='submittedpr'),# Submitted PR view
    path('tracking/', TrackingView.as_view(), name='tracking'),# Tracking view
    path('accounts/',AccountView.as_view(),name="accounts"),# Accounts view
    # path('submittedpr/<int:id>/', SubmitPr.as_view(), name='submittedpr'),
    path('update_procurement/', views.update_procurement, name='update_procurement'),# Update procurement view
    path('create_procurement/', views.create_procurement, name='create_procurement'),# Create procurement view
    path('returned/pr/',Return_PR.as_view(),name="Return_PR"),# Returned PR view here we can do modification of procurement
    path('approvedpr/', ReversedIMMView.as_view(), name='approvedpr'),# Approved PR view
    path('enquiry-create/', EnquiryFormView.as_view(), name='enquiry-create'),# Enquiry creation view
    path('upload-document/', views.upload_document, name='upload-document'),# Document upload view
    path('modify_procurement/', views.modify_procurement, name='modify_procurement'),# Modify procurement view
    path('rejectedaccounts/', RejectedAccountsView.as_view(),name="rejectedaccounts"),# Rejected accounts view
    path('comparative/',ComparativeStatement.as_view(),name='comparative'),# Comparative statement view
    path('comparative/save/', ComparativeStatement.as_view(), name='save_comparative_statement'),# Save comparative statement view
    path('negotiation/', NegotiationView.as_view(),name="negotiation"),# Negotiation view
    path('negotiation_approval/',NegotiationApproval.as_view(),name="negotiation_approval"),
    path('dpo/', Dpo.as_view(),name="dpo"),# DPO view
    path('po/', PO.as_view(),name="po"),# PO view
    path('dpo_approval/', DpoApprovalAccounts.as_view(),name="dpo_approval"),
    path('po_approval/', POApprovalView.as_view(), name="po_approval"),
    path('dpo_acc_approval/', DpoApprovalAA.as_view(),name="dpo_acc_approval"),
    path('toggle-user-status/', ToggleUserStatusView.as_view(), name='toggle_user_status'),# Toggle user status view
    # url redirections for dashboards
    path('acc_dashboard/', AccountsDashboardView.as_view(), name='acc_dashboard'),# Accounts dashboard
    path('imm_dashboard/', ImmDashboardView.as_view(), name='imm_dashboard'),# IMM dashboard
    path('indentor_dashboard/', IndentorDashboardView.as_view(), name='indentor_dashboard'),# Indentor dashboard
    path('ra_dashboard/', RADashboardView.as_view(), name='ra_dashboard'),# RA dashboard
    
    path('aa_dashboard/', AADashboardView.as_view(), name='aa_dashboard'),# AA dashboard
    path('switch-role/', views.switch_role, name='switch_role'),# Switch role view
    path('feedback/', FeedbackView.as_view(), name='feedback'),# Feedback view
    path('aa_budget/', AABudgetView.as_view(), name='aa_budget'),# AA budget view
    path('close_session/', close_session_view, name='close_session'),
    # url redirections for data pages
    path('aa_data/', AAProcurementDataView.as_view(), name='aa_data'),# AA data view
    path('ra_data/', RAProcurementDataView.as_view(), name='ra_data'),# RA data view
    path('indentor_data/', IndentorProcurementDataView.as_view(), name='indentor_data'),# Indentor data view
    path('acc_data/', AccountsProcurementDataView.as_view(), name='acc_data'),# Accounts data view
    path('imm_data/', IMMProcurementDataView.as_view(), name='imm_data'),# IMM data view
    path('payments/', AccPaymentsUploadView.as_view(), name='payments'),# Invoice upload view
    path("get_installments/", GetInstallmentData.as_view(), name="get_installments"),
    path("budget-po/", BudgetPOView.as_view(), name="budget-po"),


    # url redirection for notification functions - web browser
    path('check_notification_status/', CheckNewNotificationEntriesView.as_view(), name='checkForNewNotificationEntries'),
    # url redirection for notification functions - App
    path('notifications/procurements/', ProcurementNotificationView.as_view(), name='procurement_notifications'),
    # url redirection for Calendar Events - Accounts
    path('calendar/', CalendarEvents.as_view(), name='calendar_events'),
    # path('ceo_received/', ProcurementCEOView.as_view(), name='ceo_received'),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)# Serve media files during development