from django.urls import re_path
from . import consumers

# WebSocket URL routing configuration for Django Channels
websocket_urlpatterns = [
    # This consumer handles real-time procurement-related notifications.
    re_path(r'ws/notifications/$', consumers.ProcurementNotificationConsumer.as_asgi()),

    # Responsible for serving real-time updates to indentor users' dashboards.
    re_path(r'ws/indentor-dashboard/$', consumers.IndentorDashboardConsumer.as_asgi()),

    # Handles real-time dashboard updates for RA users.
    re_path(r'ws/ra-dashboard/$', consumers.RADashboardConsumer.as_asgi()),

    # Manages real-time dashboard updates for AA users.
    re_path(r'ws/aa-dashboard/$', consumers.AADashboardConsumer.as_asgi()),

    # Sends instant dashboard updates for IMM users.
    re_path(r'ws/imm-dashboard/$', consumers.IMMDashboardConsumer.as_asgi()),

    # Provides real-time account dashboard updates for Accounts users.
    re_path(r'ws/acc-dashboard/$', consumers.AccDashboardConsumer.as_asgi()),

    #provides real-time sidebar procurement ids 
    # re_path(r'ws/procurement_updates/$', consumers.ProcurementConsumer.as_asgi()),
    # Provides real-time tracking updates for  users.
    re_path(r'ws/sidebar/tracking/$', consumers.SidebarTrackingUpdateConsumer.as_asgi()),

    re_path(r'ws/ra-procurements/$', consumers.RAProcurementConsumer.as_asgi()),

    re_path(r'ws/reject_updates/$', consumers.RejectProcurementConsumer.as_asgi()),

    re_path(r'ws/aa_updates/$', consumers.AAProcurementConsumer.as_asgi()),

    re_path(r"ws/indentor-procurements/$", consumers.IndentorProcurementConsumer.as_asgi()),

    re_path(r'ws/enquiry/$', consumers.EnquiryProcurementConsumer.as_asgi()),

    re_path(r"ws/rejected-indentor/$", consumers.RejectedIndentorProcurementConsumer.as_asgi()),

    # re_path(r'ws/enquiry/$', consumers.EnquiryProcurementConsumer.as_asgi()),

    
    #  re_path(r'ws/procurement_updates/$', consumers.ProcurementConsumer.as_asgi()),
   
    re_path(r'ws/tracking/$', consumers.SidebarTrackingUpdateConsumer.as_asgi()),
    # Provides real-time budget updates for AA users.
    re_path(r'ws/aa-budget/$', consumers.AABudgetConsumer.as_asgi()),

      re_path(r'ws/sidebar/(?P<role>\w+)/(?P<page>\w+)/$', consumers.SidebarUpdateConsumer.as_asgi()),
]

