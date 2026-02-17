import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from django.http import HttpRequest
from .views import ProcurementNotificationView, ImmDashboardView, AccountsDashboardView
from .services.dashboard import get_indentor_dashboard_data, get_RA_dashboard_data, get_AA_dashboard_data, get_accounts_dashboard_data, get_aa_budget_data
from .models import Procurement, Project, StageProgress,  EnquiryFormPR, UserReg,VendorQuotations
from asgiref.sync import sync_to_async
from django.db.models import Max, Q
from django.utils import timezone

class ProcurementNotificationConsumer(AsyncWebsocketConsumer):
    """
        WebSocket consumer to handle real-time procurement notifications for authenticated users.
    """
    async def connect(self):
        # Retrieve the user from the connection scope
        user = self.scope["user"]
        #print(f"[NOTIFICATION WS CONNECT] User {user} connecting. Channel: {self.channel_name}")

        # Check if the user is authenticated; close connection if not
        if user is None or isinstance(user, AnonymousUser) or not user.is_authenticated:
            #print("[NOTIFICATION WS CONNECT] User not authenticated, closing connection.")
            await self.close()
            return

        # Create a unique group name for the user based on their ID
        self.group_name = f"user_{user.id}"
        # Add the current WebSocket channel to the user's group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        #print(f"[NOTIFICATION WS CONNECT] Added user to group {self.group_name}")

        # Accept the WebSocket connection
        await self.accept()

        # Fetch initial notifications for the user (database operation offloaded to thread)
        data = await self.get_notifications(user)
        #print(f"[NOTIFICATION WS CONNECT] Sending initial notifications to user {user}")

        # Send the initial notification data over the WebSocket as JSON
        await self.send(text_data=json.dumps(data))

    async def disconnect(self, close_code):
        # On disconnect, remove the channel from the user's group to stop receiving updates
        user = self.scope["user"]
        if user.is_authenticated:
            await self.channel_layer.group_discard(f"user_{user.id}", self.channel_name)

    async def receive(self, text_data):
        # This consumer currently does not handle incoming messages from the client
        pass  

    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event["data"]))

    @database_sync_to_async
    def get_notifications(self, user):
        # Fetch notifications synchronously from the Django view and return as JSON
        view = ProcurementNotificationView()
        # Create a mock request object with the user attached
        request = type('Request', (object,), {'user': user})
        response = view.get(request)
        return json.loads(response.content)


class IndentorDashboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for the Indentor Dashboard.
    - Authenticates and connects a user to a personalized WebSocket group.
    - Sends initial dashboard data immediately after connection.
    - Listens for backend-pushed updates via Django Channels and forwards them to the frontend.
    """

    async def connect(self):
        """
        Handles the WebSocket connection initiation.
        - Verifies the user's authentication.
        - Adds the connection to a user-specific group.
        - Sends initial dashboard data to the client.
        """
        user = self.scope["user"]
        #print(f"[INDENTOR DASHBOARD WS CONNECT] User {user} connecting to dashboard. Channel: {self.channel_name}")

        # Reject unauthenticated or anonymous users
        if user is None or isinstance(user, AnonymousUser) or not user.is_authenticated:
            #print("[INDENTOR DASHBOARD WS CONNECT] User not authenticated for dashboard, closing connection.")
            await self.close()
            return

        # Define a unique group name for the user for targeted updates
        self.group_name = f"dashboard_user_{user.id}"

        # Add this WebSocket connection to the user's group
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        # Accept the WebSocket connection
        await self.accept()

        # Fetch and send the initial dashboard data to the frontend
        data = await self.get_indentor_initial_dashboard_data(user)
        await self.send(text_data=json.dumps(data))  # Ensure JSON-serializable format

    async def disconnect(self, close_code):
        """
        Handles WebSocket disconnection.
        - Removes the user from their assigned group to stop future updates.
        """
        user = self.scope["user"]
        if user and user.is_authenticated:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_indentor_dashboard_update(self, event):
        """
        Receives and sends dashboard updates triggered via Django signals
        """
        await self.send(text_data=json.dumps(event["data"])) 

    @database_sync_to_async
    def get_indentor_initial_dashboard_data(self, user):
        """
        Fetches the initial dashboard context data for the indentor.
        """
        data = get_indentor_dashboard_data(user)
        return data

class RADashboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for the RA dashboard.
    - Authenticates the connecting user.
    - Assigns the user to a unique WebSocket group for personalized updates.
    - Sends initial dashboard data upon successful connection.
    - Listens for real-time updates pushed from the backend via Django Channe;s.
    """

    async def connect(self):
        """
        Handles a new WebSocket connection request.
        - Verifies that the user is authenticated.
        - Joins a personalized group to receive real-time updates.
        - Sends initial dashboard data immediately upon connection.
        """
        user = self.scope["user"]
        #print(f"[RA DASHBOARD WS CONNECT] User {user} connecting to dashboard. Channel: {self.channel_name}")

        # Close the connection if the user is not logged in or is anonymous
        if user is None or isinstance(user, AnonymousUser) or not user.is_authenticated:
            #print("[RA DASHBOARD WS CONNECT] User not authenticated for dashboard, closing connection.")
            await self.close()
            return

        # Define a unique group name for this RA user (used for signal updates)
        self.group_name = f"dashboard_ra_user_{user.id}"

        # Add this WebSocket channel to the user-specific group
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        # Accept the WebSocket connection
        await self.accept()

        # Fetch and send initial dashboard data to the frontend
        data = await self.get_RA_initial_dashboard_data(user)
        await self.send(text_data=json.dumps(data))  # Ensure JSON serialization

    async def disconnect(self, close_code):
        """
        Handles WebSocket disconnection.
        Removes the channel from the RA user's group to stop receiving updates.
        """
        user = self.scope["user"]
        if user and user.is_authenticated:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_ra_dashboard_update(self, event):
        """
        Sends real-time dashboard updates to the frontend.
        Triggered by backend signals publishing to the RA user's WebSocket group.
        """
        await self.send(text_data=json.dumps(event["data"]))  # Forward data to the frontend

    @database_sync_to_async
    def get_RA_initial_dashboard_data(self, user):
        """
        Fetches initial dashboard data for the RA user.
        Called asynchronously to avoid blocking the WebSocket event loop.
        Uses existing utility function `get_RA_dashboard_data(user)`.
        """
        data = get_RA_dashboard_data(user)
        return data

class AADashboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for the AA dashboard.
    - Authenticates the connecting user.
    - Subscribes them to a unique group for real-time dashboard updates.
    - Sends initial dashboard data upon connection.
    - Listens for backend-pushed updates via Django Channels.
    """

    async def connect(self):
        """
        Called when a WebSocket connection is initiated.
        Verifies user authentication, assigns them to a group, and sends initial dashboard data.
        """
        user = self.scope["user"]
        #print(f"[AA DASHBOARD WS CONNECT] User {user} connecting to dashboard. Channel: {self.channel_name}")

        # Reject the connection if user is not authenticated
        if user is None or isinstance(user, AnonymousUser) or not user.is_authenticated:
            #print("[AA DASHBOARD WS CONNECT] User not authenticated for dashboard, closing connection.")
            await self.close()
            return

        # Define a unique group name for the authenticated user
        self.group_name = f"dashboard_aa_user_{user.id}"

        # Add the user's WebSocket channel to the group
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        # Accept the WebSocket connection
        await self.accept()

        # Send initial dashboard data to the user
        data = await self.get_AA_initial_dashboard_data(user)

        # Ensure the data is JSON serializable
        await self.send(text_data=json.dumps(data)) 

    async def disconnect(self, close_code):
        """
        Called when the WebSocket connection is closed.
        Removes the user's channel from their assigned group.
        """
        user = self.scope["user"]
        if user and user.is_authenticated:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_aa_dashboard_update(self, event):
        """
        Handler for events sent to the user's group.
        Sends updated dashboard data to the frontend.
        """
        await self.send(text_data=json.dumps(event["data"]))

    @database_sync_to_async
    def get_AA_initial_dashboard_data(self, user):
        """
        Fetches the initial dashboard context data for the AA user.
        This function is executed asynchronously to avoid blocking the event loop.
        """
        data = get_AA_dashboard_data(user)
        return data   

class IMMDashboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for the IMM dashboard.
    - Authenticates the connecting user.
    - Subscribes the user to a personal WebSocket group.
    - Sends initial dashboard data on connection.
    - Listens for real-time updates pushed to the group (via Django signals).
    """

    async def connect(self):
        """
        Handles a new WebSocket connection.
        Authenticates the user and adds them to a user-specific group.
        Sends initial dashboard data upon successful connection.
        """
        user = self.scope["user"]
        #print(f"[IMM DASHBOARD WS CONNECT] User {user} connecting to dashboard. Channel: {self.channel_name}")

        # Reject connection if user is not authenticated
        if user is None or isinstance(user, AnonymousUser) or not user.is_authenticated:
            #print("[IMM DASHBOARD WS CONNECT] User not authenticated for dashboard, closing connection.")
            await self.close()
            return

        # Assign user to a personal group for receiving updates
        self.group_name = f"dashboard_imm_user_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        # Accept the WebSocket connection
        await self.accept()

        # Send initial dashboard data to frontend
        data = await self.get_IMM_initial_dashboard_data(user)

        # Ensure all data is JSON serializable
        await self.send(text_data=json.dumps(data, default=str))  

    async def disconnect(self, close_code):
        """
        Handles WebSocket disconnection.
        Removes the user's channel from their personal group.
        """
        user = self.scope["user"]
        if user and user.is_authenticated:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_imm_dashboard_update(self, event):
        """
        Called when a signal pushes a message to the user's group.
        Forwards updated dashboard data to the frontend.
        """
        await self.send(text_data=json.dumps(event["data"], default=str))  # Send update to frontend

    @database_sync_to_async
    def get_IMM_initial_dashboard_data(self, user):
        """
        Prepares initial IMM dashboard data using the ImmDashboardView context.
        This simulates a view call with a dummy HttpRequest for the authenticated user.
        """
        # Create a mock request object to simulate a view call
        request = HttpRequest()
        request.user = user

        # Instantiate and set up the dashboard view manually
        view = ImmDashboardView()
        view.setup(request)

        # Get the dashboard context
        context = view.get_context_data()

        # Remove non-serializable data like the view instance
        context_data = {
            key: value for key, value in context.items()
            if key != 'view'
        }
        return context_data

class AccDashboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer that handles real-time communication for the Accounts Dashboard.
    - Authenticated users from the "Accounts" role connect to receive live updates.
    - Supports initial dashboard data push and filtered data fetching.
    - Receives updates from Django signals via the channel layer.
    """

    async def connect(self):
        """
        Called when a WebSocket connection is established.
        Authenticates the user, assigns them to a group based on their ID,
        and sends initial dashboard data.
        """
        user = self.scope["user"]
        #print(f"[ACC DASHBOARD WS CONNECT] User {user} connecting to dashboard. Channel: {self.channel_name}")

        # Reject connection if user is not authenticated
        if user is None or isinstance(user, AnonymousUser) or not user.is_authenticated:
            #print("[ACC DASHBOARD WS CONNECT] User not authenticated, closing connection.")
            await self.close()
            return

        self.user = user
        self.group_name = f"dashboard_acc_user_{user.id}"  # Unique group name for this user

        # Add the WebSocket channel to the user's group
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        # Accept the connection
        await self.accept()

        # send initial dashboard data immediately after connection
        # data = await self.get_ACC_initial_dashboard_data(user)
        # await self.send(text_data=json.dumps({
        #     "type": "budget_data",
        #     "data": data
        # }, default=str))

    async def disconnect(self, close_code):
        """
        Called when the WebSocket connection is closed.
        Removes the user's channel from the group to stop further updates.
        """
        if hasattr(self, 'user') and self.user and self.user.is_authenticated:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """
        Handles messages received from the frontend over WebSocket.
        - "fetch_budget": fetches filtered dashboard data.
        """
        try:
            data = json.loads(text_data)
            action = data.get("action")

            if action == "fetch_budget":
                fy = data.get("financial_year")
                quarter = data.get("quarter")
                source_filter = data.get("source_filter", "all")

                # Validate input parameters
                if not fy or not quarter:
                    await self.send(text_data=json.dumps({
                        "type": "error",
                        "message": "Missing financial year or quarter."
                    }))
                    return

                # Fetch filtered budget data and send back to frontend
                response_data = await self.get_ACC_dashboard_data_by_filters(self.user, fy, quarter, source_filter)
                await self.send(text_data=json.dumps({
                    "type": "budget_data",
                    "data": response_data
                }, default=str))

        except Exception as e:
            # Catch and report any unexpected errors
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": f"Exception occurred: {str(e)}"
            }))

    async def send_acc_dashboard_update(self, event):
        """
        Receives real-time updates from the backend via Django signals and pushes them to the frontend.
        Triggered when the group (this user) receives a `send_acc_dashboard_update` event.
        """
        await self.send(text_data=json.dumps({
            "type": "budget_data",
            "data": event["data"]
        }, default=str))

    @database_sync_to_async
    def get_ACC_initial_dashboard_data(self, user):
        """
        Synchronously fetches initial dashboard data using the helper function.
        Called from async context via decorator.
        """
        return get_accounts_dashboard_data(user)

    @database_sync_to_async
    def get_ACC_dashboard_data_by_filters(self, user, financial_year, quarter, source_filter):
        """
        Synchronously fetches dashboard data based on filter inputs.
        """
        return get_accounts_dashboard_data(user, financial_year, quarter, source_filter)

class AABudgetConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer that handles real-time communication for the AA Budget Page.
    - Authenticated users from the "AA" role connect to receive live updates.
    - Supports initial dashboard data push and filtered data fetching.
    - Receives updates from Django signals via the channel layer.
    """

    async def connect(self):
        """
        Called when a WebSocket connection is established.
        Authenticates the user, assigns them to a group based on their ID,
        and sends initial data.
        """
        user = self.scope["user"]
        #print(f"[AA BUDGET WS CONNECT] User {user} connecting to the budget page. Channel: {self.channel_name}")

        # Reject connection if user is not authenticated
        if user is None or isinstance(user, AnonymousUser) or not user.is_authenticated:
            #print("[AA BUDGET WS CONNECT] User not authenticated, closing connection.")
            await self.close()
            return

        self.user = user
        self.group_name = f"budget_aa_user_{user.id}"  # Unique group name for this user

        # Add the WebSocket channel to the user's group
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        # Accept the connection
        await self.accept()

        # send initial dashboard data immediately after connection
        # data = await self.get_ACC_initial_dashboard_data(user)
        # await self.send(text_data=json.dumps({
        #     "type": "budget_data",
        #     "data": data
        # }, default=str))

    async def disconnect(self, close_code):
        """
        Called when the WebSocket connection is closed.
        Removes the user's channel from the group to stop further updates.
        """
        if hasattr(self, 'user') and self.user and self.user.is_authenticated:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """
        Handles messages received from the frontend over WebSocket.
        - "fetch_budget": fetches filtered dashboard data.
        """
        try:
            data = json.loads(text_data)
            action = data.get("action")

            if action == "fetch_aa_budget":
                fy = data.get("financial_year")
                quarter = data.get("quarter")
                source_filter = data.get("source_filter", "all")

                # Validate input parameters
                if not fy or not quarter:
                    await self.send(text_data=json.dumps({
                        "type": "error",
                        "message": "Missing financial year or quarter."
                    }))
                    return

                # Fetch filtered budget data and send back to frontend
                response_data = await self.get_AA_budget_data_by_filters(self.user, fy, quarter, source_filter)
                await self.send(text_data=json.dumps({
                    "type": "aa_budget_data",
                    "data": response_data
                }, default=str))

        except Exception as e:
            # Catch and report any unexpected errors
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": f"Exception occurred: {str(e)}"
            }))

    async def send_aa_budget_update(self, event):
        """
        Receives real-time updates from the backend via Django signals and pushes them to the frontend.
        Triggered when the group (this user) receives a `send_aa_budget_update` event.
        """
        await self.send(text_data=json.dumps({
            "type": "aa_budget_data",
            "data": event["data"]
        }, default=str))

    @database_sync_to_async
    def get_AA_initial_dashboard_data(self, user):
        """
        Synchronously fetches initial dashboard data using the helper function.
        Called from async context via decorator.
        """
        return get_aa_budget_data(user)

    @database_sync_to_async
    def get_AA_budget_data_by_filters(self, user, financial_year, quarter, source_filter):
        """
        Synchronously fetches dashboard data based on filter inputs.
        """
        return get_aa_budget_data(user, financial_year, quarter, source_filter)
  
class ProcurementConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "procurement_updates"
        
        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        await self.send_initial_procurements()

    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        pass

    async def send_procurement_updates(self, event):
        procurements = await self.get_procurements()
        
        await self.send(text_data=json.dumps({
            'type': 'procurement_update',
            'procurements': procurements
        }))

    async def send_initial_procurements(self):
        procurements = await self.get_procurements()
        await self.send(text_data=json.dumps({
            'type': 'initial_data',
            'procurements': procurements
        }))

    @sync_to_async
    def get_procurements(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            return {
                "user_details": {},
                "procurements": []
            }
        immpr = list(StageProgress.objects.filter(
            stagename__stage="stage6",
            remarktype="Enquiry Generated"
        ).values_list("procurement_id__procurement_id", flat=True).distinct())
 
        procurements = Procurement.objects.filter(
            procurement_id__in=immpr,
            imm_user=user
        ).annotate(
            latest_stage_datetime=Max(
                'prid__datetime',
                filter=Q(prid__stagename__stage='stage6', prid__remarktype='Enquiry Generated')
            )
        ).order_by('-latest_stage_datetime', '-id').select_related('project', 'user')
        try:
            user_reg = UserReg.objects.get(user=user)
            dept_name = user_reg.user_dept.dept_name if user_reg.user_dept else 'N/A'
            roles = user_reg.role.all()
            role_names = [role.role for role in roles]
        except UserReg.DoesNotExist:
            dept_name = 'N/A'
            role_names = []
 
        user_details = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_authenticated': user.is_authenticated,
            'department': dept_name,
            'roles': role_names,
            'role_display': ', '.join(role_names) if role_names else 'N/A',
        }     

 
        procurements_data = []
        for procurement in procurements:
            procurement.procurement_title = procurement.procurement_title
            try:
                enquiry_form = EnquiryFormPR.objects.get(procure__procurement_id=procurement.procurement_id)
                has_quotations = VendorQuotations.objects.filter(eqno=enquiry_form).exists()
            except EnquiryFormPR.DoesNotExist:
                has_quotations = False
 
            if has_quotations:
                latest_stage = StageProgress.objects.filter(
                    procurement_id__procurement_id=procurement.procurement_id
                ).values("stagename__stage", "remarktype").last()
 
                action_performed = (
                    latest_stage["stagename__stage"] == "stage6" and
                    latest_stage["remarktype"] == "Enquiry Generated"
                )
 
                procurements_data.append({
                    'id': procurement.id,
                    'procurement_id': procurement.procurement_id,
                    'datetime': timezone.localtime(procurement.datetime).strftime("%d-%m-%Y %H:%M:%S") if procurement.datetime else "",
                    'project_name': procurement.project.name if procurement.project else "",
                    'username': procurement.user.username if procurement.user else "",
                    'action_performed': action_performed,
                    'is_active': False,
                    'procurement_title': procurement.procurement_title,
                })
 
            return {
                "user_details": user_details,
                "procurements": procurements_data
            }
# sidebarTrackingUpdate
class SidebarTrackingUpdateConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
            await self.close()
            return
 
        group_name = f"tracking_{user.id}"
        await self.channel_layer.group_add(group_name, self.channel_name)
        #print('Subscribed to group:', group_name)
 
        await self.accept()
 
    async def disconnect(self, close_code):
        for group_name in self.group_names:
            await self.channel_layer.group_discard(group_name, self.channel_name)
 
 
    async def send_initial_data(self, event):
        await self.send(text_data=json.dumps(event["data"]))


class RAProcurementConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_authenticated:
            self.group_name = f"receive_ra_user_{user.id}"
            #print(self.group_name,'WebSocket connected for RA dashboard.')
            # Add this channel to the group for this user
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        # Remove channel from the group on disconnect
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # This method handles messages sent to the group
    async def send_procurement_update(self, event):
        # The event should have a "data" key containing JSON-serializable data
        #print('event',event["data"])

        await self.send(text_data=json.dumps(event["data"]))



class RejectProcurementConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_authenticated:
            self.group_name = f"reject_ra_user_{user.id}"
            #print(f"{self.group_name} WebSocket connected for reject updates.")
            # Add this channel to the group for this user
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        # Remove channel from the group on disconnect
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Receive message from group
    async def send_procurement_ra(self, event):
        # Send the JSON data to WebSocket client
        await self.send(text_data=json.dumps(event["data"]))


class AAProcurementConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]

        if user.is_authenticated:
            self.group_name = f"aa_user_{user.id}"

            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )

            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        user = self.scope["user"]
        if user.is_authenticated:
            await self.channel_layer.group_discard(
                f"aa_user_{user.id}",
                self.channel_name
            )

    async def send_procurement_aa(self, event):
        await self.send(text_data=json.dumps(event["data"]))


# consumers.py
class IndentorProcurementConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]

        if user.is_authenticated:
            self.group_name = f"indentor_user_{user.id}"

            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )

            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        user = self.scope["user"]
        if user.is_authenticated:
            await self.channel_layer.group_discard(
                f"indentor_user_{user.id}",
                self.channel_name
            )

    async def send_procurement_indentor(self, event):
        await self.send(text_data=json.dumps(event["data"]))


class RejectedIndentorProcurementConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]

        if user.is_authenticated:
            self.group_name = f"rejected_indentor_user_{user.id}"

            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        user = self.scope["user"]
        if user.is_authenticated:
            await self.channel_layer.group_discard(
                f"rejected_indentor_user_{user.id}",
                self.channel_name
            )

    async def send_procurement_indentor_reject(self, event):
        """
        This method is triggered when a rejected procurement is returned to stage1.
        """
        await self.send(text_data=json.dumps(event["data"]))




class EnquiryProcurementConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]

        if user.is_authenticated:
            self.group_name = f"enquiry_user_{user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            #print(f"✅ WebSocket connection established for user {user.id} in group {self.group_name}")
        else:
            #print("❌ WebSocket connection denied (unauthenticated user)")
            await self.close()

    async def disconnect(self, close_code):
        user = self.scope["user"]
        if user.is_authenticated:
            await self.channel_layer.group_discard(f"enquiry_user_{user.id}", self.channel_name)
            #print(f"🔌 WebSocket disconnected for user {user.id}")

    async def send_procurement_enquiry(self, event):
        #print(f"📤 Sending message to frontend: {event['data']}")
        await self.send(text_data=json.dumps(event["data"]))

# class EnquiryProcurementConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         user = self.scope["user"]

#         if user.is_authenticated:
#             self.group_name = f"enquiry_user_{user.id}"

#             # Join group
#             await self.channel_layer.group_add(
#                 self.group_name,
#                 self.channel_name
#             )

#             await self.accept()
#         else:
#             await self.close()

#     async def disconnect(self, close_code):
#         user = self.scope["user"]

#         if user.is_authenticated:
#             await self.channel_layer.group_discard(
#                 f"enquiry_user_{user.id}",
#                 self.channel_name
#             )

#     async def send_procurement_enquiry(self, event):
#         import logging
#         logging.warning(f"SENDING EVENT TO IMM: {event}")
#         """
#         Called by the signal to send procurement update to IMM user
#         """
#         await self.send(text_data=json.dumps(event["data"]))





class SidebarUpdateConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
            await self.close()
            return

        role = self.scope["url_route"]["kwargs"]["role"]

        # Subscribe to all pages user cares about
        pages = ['accounts', 'imm', 'negotiation', 'dpo','rejectedimm','rejectedaccounts','po']  # add your pages here

        self.group_names = []
        for page in pages:
            group_name = f"sidebar_{role}_{page}_user_{user.id}"
            await self.channel_layer.group_add(group_name, self.channel_name)
            self.group_names.append(group_name)
            #print('Subscribed to group:', group_name)

        await self.accept()

    async def disconnect(self, close_code):
        for group_name in self.group_names:
            await self.channel_layer.group_discard(group_name, self.channel_name)


    async def send_sidebar_update(self, event):
        await self.send(text_data=json.dumps(event["data"]))