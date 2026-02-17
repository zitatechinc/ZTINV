# signals.py

import json
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import HttpRequest
import pytz
from .models import StageProgress, BudgetAllocation, Procurement, UserReg, Project, Vendor, Purchase_Order, QuotationParticular, EnquiryFormPR,ModifiedPr

from ims.services.files import get_indentor_procurement_subdata
from .models import StageProgress, BudgetAllocation, Procurement, UserReg, Project, Vendor, Purchase_Order
from .views import ProcurementNotificationView, ImmDashboardView
from .services.dashboard import get_aa_budget_data, get_indentor_dashboard_data,get_RA_dashboard_data, get_AA_dashboard_data, get_accounts_dashboard_data
import pytz
from django.utils.timezone import localtime
from .models import StageProgress, Procurement, DPO


@receiver([post_save, post_delete], sender=StageProgress)
def notify_procurement_users(sender, instance, **kwargs):
    """
    Signal handler triggered after a StageProgress instance is saved.
    Sends real-time notifications to relevant procurement users via Django Channels.
    """
    procurement = instance.procurement_id  # Related procurement object

    # List of users to notify about the update 
    users_to_notify = [
        procurement.ra_user,
        procurement.imm_user,
        procurement.account_user,
        procurement.aa_user,
        procurement.user,
    ]

    # #print("Users to be notified: ", users_to_notify)

    # Notify each user via their user-specific Channels group
    for user in users_to_notify:
        if user:
            layer = get_channel_layer()  # Get the channel layer for sending messages

            # Prepare a request with user attached to call the view for notifications
            view = ProcurementNotificationView()
            request = type('Request', (object,), {'user': user})
            response = view.get(request)

            data = response.content  # Get serialized notification data

            # Send notification asynchronously to the user's group, synchronously wrapped for signals
            async_to_sync(layer.group_send)(
                f"user_{user.id}",  # Group name per user ID
                {
                    "type": "send_notification",  # This must match the method in the consumer
                    "data": json.loads(data)      # Notification payload as dict
                }
            )
            
@receiver([post_save, post_delete], sender=StageProgress)
def send_indentor_dashboard_update(sender, instance, **kwargs):
    """
        Django signal receiver that listens for both post_save and post_delete events on the StageProgress model
        to update the indentor dashboard with real-time data
    """
    # Get the related procurement object from the StageProgress instance
    procurement = instance.procurement_id
    # Get the user who created the procurement
    procurement_user = procurement.user 

    # If no user is associated with the procurement, skip sending the update
    if not procurement_user:
        # #print("Procurement creator user not found, skipping update.")
        return

    # Prepare dashboard data for the indentor user
    message = get_indentor_dashboard_data(procurement_user)

    # Define the channel group name for the user's dashboard updates
    group_name = f"dashboard_user_{procurement_user.id}"

    # Get the Django Channels channel layer (used for WebSocket communication)
    channel_layer = get_channel_layer()

    # Send the dashboard update message to the user's WebSocket group
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "send_indentor_dashboard_update", # This must match the method in the consumer
            "data": message  # Dashboard data payload
        }
    )

@receiver([post_save, post_delete], sender=StageProgress)
def send_ra_dashboard_update(sender, instance, **kwargs):
    """
        Django signal receiver that listens for both post_save and post_delete events on the StageProgress model
        to update the RA dashboard with real-time data
    """
    # Get the related procurement object from the StageProgress instance
    procurement = instance.procurement_id
    
    # Get the related procurement related RA user to be notified 
    procurement_user = procurement.ra_user 

    # If no user is associated with the procurement, skip sending the update
    if not procurement_user:
        # #print("Procurement related RA user not found, skipping update.")
        return

    # Prepare dashboard data for the RA user 
    message = get_RA_dashboard_data(procurement_user)
    
    # Define the channel group name for the RA's dashboard updates
    group_name = f"dashboard_ra_user_{procurement_user.id}"

    # Get the Django Channels channel layer (used for WebSocket communication)
    channel_layer = get_channel_layer()

    # Send the dashboard update message to the RA's WebSocket group
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "send_ra_dashboard_update", # This must match the method in the consumer
            "data": message # Dashboard data payload
        }
    )

@receiver([post_save, post_delete], sender=StageProgress)
def send_aa_dashboard_update(instance, **kwargs):
    """
        Django signal receiver that listens for both post_save and post_delete events on the StageProgress model 
        and BudgetAllocation Model to update the AA dashboard with real-time data
    """
    aa_users = set()

    # If signal is from Procurement Model - add the procurement related aa_user
    if isinstance(instance, Procurement):
        if instance.aa_user:
            aa_users.add(instance.aa_user)

    # If signal is from BudgetAllocation - fetch the projects and its related procurements and get the aa_user
    elif isinstance(instance, BudgetAllocation):
        project = instance.project
        if project:
            procurements = Procurement.objects.filter(
                project=project,
                is_draft=False,
                cancellation=False
            ).select_related('aa_user')

            for procurement in procurements:
                if procurement.aa_user:
                    aa_users.add(procurement.aa_user)

    # If the model has a procurement_id attribute (e.g., StageProgress)
    elif hasattr(instance, 'procurement_id') and instance.procurement_id:
        procurement = instance.procurement_id
        if procurement.aa_user:
            aa_users.add(procurement.aa_user)

    # Now send update for each AA user
    if not aa_users:
        # #print("No AA users found for update, skipping.")
        return

    # Get the Django Channels channel layer (used for WebSocket communication)
    channel_layer = get_channel_layer()

    for aa_user in aa_users:
        
        # Prepare dashboard data for the AA user 
        message = get_AA_dashboard_data(aa_user)
        # #print("aa" , message)

        # Define the channel group name for the AA's dashboard updates
        group_name = f"dashboard_aa_user_{aa_user.id}"

        # Send the dashboard update message to the AA's WebSocket group
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_aa_dashboard_update", # This must match the method in the consumer
                "data": message # Dashboard data payload
            }
        )

@receiver([post_save, post_delete], sender=StageProgress)
def stage_progress_handler(sender, instance, **kwargs):
    # update the AA dashboard whenever a Stage Progress is changed
    send_aa_dashboard_update(instance)


@receiver([post_save, post_delete], sender=BudgetAllocation)
def budget_allocation_handler(sender, instance, **kwargs):
    # update the AA dashboard whenever a budget allocation is changed
    send_aa_dashboard_update(instance)


@receiver([post_save, post_delete], sender=StageProgress)
@receiver([post_save, post_delete], sender=Project)
@receiver([post_save, post_delete], sender=Vendor)
def send_imm_dashboard_update(sender, instance, **kwargs):
    """
        Django signal receiver that listens for both post_save and post_delete events on the StageProgress model,
        Project Model, Vendor Model to update the IMM dashboard with real-time data
    """
        
    # Get the Django Channels channel layer (used for WebSocket communication)
    layer = get_channel_layer()

    # Get all the IMM users
    imm_users = UserReg.objects.filter(role__role="IMM").select_related("user")
    if not imm_users.exists():
        return  # No IMM users, nothing to send

    # Use one of the IMM users to prepare the dashboard context
    dummy_user = imm_users.first()

    # Simulate an HttpRequest with the IMM user to generate dashboard data
    request = HttpRequest()
    request.user = dummy_user

    # Manually set up the IMM dashboard view to fetch context data
    view = ImmDashboardView()
    view.setup(request)
    view.request = request
    context = view.get_context_data()

    # Remove the 'view' key from the context to avoid serialization issues
    context_data = {
        key: value for key, value in context.items()
        if key != 'view'
    }

    # Send the dashboard update to each IMM user's WebSocket group
    for user in imm_users:

        # WebSocket group name per user
        group_name = f"dashboard_imm_user_{user.user.id}" 

        # Send the message to the WebSocket group using Django Channels
        async_to_sync(layer.group_send)(
            group_name,
            {
                "type": "send_imm_dashboard_update",  # This must match the method in the consumer
                "data": context_data                  # Dashboard Data Payload
            }
        )

@receiver([post_save, post_delete], sender=BudgetAllocation)
@receiver([post_save, post_delete], sender=Purchase_Order)
def send_acc_dashboard_update(sender, instance, **kwargs):
    """
        Django signal receiver that listens for both post_save and post_delete events on the BudgetAllocation model,
        to update the Accounts dashboard with real-time data
    """

    # Get the channel layer for WebSocket communication
    layer = get_channel_layer()

    # Retrieve all users with the "Accounts" role
    acc_users = UserReg.objects.filter(role__role="Accounts").select_related("user")

    # If no Accounts users exist, exit early (no one to notify)
    if not acc_users.exists():
        return

    # Use the first Accounts user to generate a common dashboard context
    # This assumes dashboard data is the same for all Accounts users
    dummy_user = acc_users.first().user

    # Generate the dashboard data for Accounts users
    context_data = get_accounts_dashboard_data(dummy_user)

    # Loop through each Accounts user and send the data to their WebSocket group
    for acc_user in acc_users:
        
        # WebSocket group for the user
        group_name = f"dashboard_acc_user_{acc_user.user.id}" 

        # Send the context data to the group using Django Channels
        async_to_sync(layer.group_send)(
            group_name,
            {
                "type": "send_acc_dashboard_update",  # This must match the method in the consumer
                "data": context_data                  # Dashboard data payload
            }
        )

@receiver([post_save, post_delete], sender=BudgetAllocation)
@receiver([post_save, post_delete], sender=Purchase_Order)
def send_aa_budget_update(sender, instance, **kwargs):
    """
        Django signal receiver that listens for both post_save and post_delete events on the BudgetAllocation model,
        to update the budget page with real-time data
    """

    # Get the channel layer for WebSocket communication
    layer = get_channel_layer()

    # Retrieve all users with the "Accounts" role
    aa_users = UserReg.objects.filter(role__role="Approving Authority").select_related("user")

    # If no Accounts users exist, exit early (no one to notify)
    if not aa_users.exists():
        return

    # Use the first Accounts user to generate a common dashboard context
    # This assumes dashboard data is the same for all Accounts users
    dummy_user = aa_users.first().user

    # Generate the dashboard data for Accounts users
    context_data = get_aa_budget_data(dummy_user)

    # Loop through each Accounts user and send the data to their WebSocket group
    for aa_user in aa_users:
        
        # WebSocket group for the user
        group_name = f"budget_aa_user_{aa_user.user.id}" 

        # Send the context data to the group using Django Channels
        async_to_sync(layer.group_send)(
            group_name,
            {
                "type": "send_aa_budget_update",  # This must match the method in the consumer
                "data": context_data                  # Dashboard data payload
            }
        )

@receiver(post_save, sender=StageProgress)
@receiver(post_delete, sender=StageProgress)
@receiver(post_save, sender=QuotationParticular)
@receiver(post_delete, sender=QuotationParticular)
@receiver(post_save, sender=EnquiryFormPR)
@receiver(post_delete, sender=EnquiryFormPR)
def notify_procurement_update(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    try:
        async_to_sync(channel_layer.group_send)(
            "procurement_updates",
            {
                "type": "send_procurement_updates",
                
            }
        )
    except Exception as e:
        print(f"Error sending procurement update: {str(e)}")


def get_all_roles_for_user(user):
    if hasattr(user, 'userreg'):
        return list(user.userreg.role.values_list('role', flat=True))
    return []

 
# Helper function to get employee ID (similar to your view)
def get_emp_id(user):
        """Helper method to get employee ID from User object"""
        if user and hasattr(user, 'userreg'):
            return user.userreg.emp_id
        return 'N/A'


@receiver([post_save, post_delete], sender=StageProgress)
def procurement_update_handler(sender, instance, **kwargs):
    # Get all users associated with this procurement
    procurement = instance.procurement_id
    user_roles = get_all_roles_for_user(instance.user)
    users = set()
   
    # Add all users from procurement
    for field in ['user', 'ra_user', 'imm_user', 'account_user', 'aa_user']:
        user = getattr(procurement, field, None)
        if user:
            users.add(user)
   
    # Prepare the full data structure
    ist = pytz.timezone('Asia/Kolkata')
    created_datetime = procurement.datetime.astimezone(ist).strftime('%d-%m-%Y %I:%M %p')
   
    # Get stage progress data
    stage_progress_entries = StageProgress.objects.filter(
        procurement_id=procurement.id
    ).order_by('datetime')

    STAGE_ORDER = [
        'stage1', 'stage2', 'stage3', 'stage4', 'stage5',
        'stage6', 'stage7', 'stage1','stage8', 'stage9', 'stage10'
    ]

    # Define the normal stage progression
    stage_to_user_attr_map = {
        'stage1': 'user',        # Indentor
        'stage2': 'ra_user',     # Recommending Authority
        'stage3': 'imm_user',   # IMM
        'stage4': 'account_user',# Accounts
        'stage5': 'aa_user',    # Approving Authority
        'stage6': 'imm_user',   # IMM (for PO generation)
        'stage7': 'imm_user',   # IMM (for other actions)
        'stage8': 'imm_user',   # IMM (for negotiation)
        'stage9': 'imm_user',   # IMM (for DPO)
        'stage10': 'imm_user',   # IMM (final stage)
    }
    DUAL_ROLE_OVERRIDES = {
        # When RA+Indentor raises PR, next should be IMM (skip RA)
        ('stage1', 'Recommending Authority'): 'imm_user',
        # When IMM+Indentor raises PR, next should be IMM (skip self)
        ('stage1', 'IMM'): 'imm_user',
        # When Accounts+Indentor raises PR, next should be IMM (skip Accounts)
        ('stage1', 'Accounts'): 'imm_user',
        # When AA+Indentor raises PR, next should be IMM (skip AA)
        ('stage1', 'Approving Authority'): 'imm_user',
    }
    stages_with_status = []
    for entry in stage_progress_entries:
        stage_datetime = entry.datetime.astimezone(ist).strftime('%d-%m-%Y %H:%M:%S')
        action_user = None
        action_type = 'action'
        #print(entry.rejectuser)
        if entry.remarktype.lower() == 'reject':
            action_user = entry.rejectuser
            action_type = 'reject'
        else:
            action_user = entry.user
        try:    
            print("reg", action_user.userreg)
        except Exception as err:
            print("::::::::::::",err)
        stages_with_status.append({
            'stage': entry.stagename.stage,
            'status': entry.remarktype.lower(),
            'datetime': stage_datetime,
            'comment': entry.remarks or '',
            'action_user': {
                'name': action_user.get_full_name() if action_user else 'N/A',
                'emp_id': get_emp_id(action_user),
            } if action_user else None,
            'action_type': action_type
        })
            
        # Handle returned and next pending stages
        if stages_with_status:
            last_stage = stages_with_status[-1]['stage']
            last_status = stages_with_status[-1]['status']
            last_action_user = stages_with_status[-1].get('action_user')

            try:
                last_stage_index = STAGE_ORDER.index(last_stage)
                next_stage_index = last_stage_index + 1
                if last_status in ('reject', 'returned'):
                    # Use last reject entry’s rejectstage and rejectuser
                    last_reject_entry = StageProgress.objects.filter(
                        procurement_id=procurement.id,
                        remarktype__iexact='reject'
                    ).order_by('-datetime').first()

                    if last_reject_entry and last_reject_entry.rejectstage:
                        returned_to_stage_name = last_reject_entry.rejectstage.stage
                        returned_to_user = last_reject_entry.rejectuser
                        # #print("reg-ret", returned_to_user.userreg)

                        returned_to_user_info = {
                            'name': returned_to_user.get_full_name() if returned_to_user else 'N/A',
                            'emp_id': get_emp_id(returned_to_user)
                        }

                        stages_with_status.append({
                            'stage': returned_to_stage_name,
                            'status': 'pending',
                            'datetime': stages_with_status[-1]['datetime'],
                            'comment': '',
                            'next_user': returned_to_user_info
                        })

                
                else:
                    
                    # Handle normal forward progression
                    if next_stage_index < len(STAGE_ORDER):
                        next_stage_name = STAGE_ORDER[next_stage_index]
                        
                        # Default to normal stage progression
                        user_field = stage_to_user_attr_map.get(next_stage_name)
                        
                        # Check for dual-role override conditions
                        if (last_stage == 'stage1' and last_status in ('pr_raised', 'modified','approval') and 
                            last_action_user and len(user_roles) > 1):

                            
                            # Get roles for procurement raised user
                            procurement_user_roles = get_all_roles_for_user(procurement.user)
                            # #print(procurement_user_roles)
                            
                            # Only apply skipping if user has exactly 2 roles and one is 'Indentor'
                            if len(procurement_user_roles) == 2 and 'Indentor' in procurement_user_roles:
                                # Determine stages to skip based on second role (other than Indentor)
                                other_roles = [r for r in procurement_user_roles if r != 'Indentor']
                                if other_roles:
                                    role = other_roles[0]  # since exactly 2 roles
                                    
                                    # Define stages to skip based on role
                                    stages_to_skip = set()
                                    if role == 'Recommending Authority':
                                        stages_to_skip.add('stage2')
                                    elif role == 'IMM':
                                        stages_to_skip.update(['stage2', 'stage3'])
                                    elif role == 'Accounts':
                                        stages_to_skip.add('stage2')
                                    elif role == 'Approving Authority':
                                        stages_to_skip.add('stage2')

                                    # Recalculate the effective stage order excluding skipped stages
                                    effective_stage_order = [stage for stage in STAGE_ORDER if stage not in stages_to_skip]
                                    
                                    # Find index of last_stage in filtered list and set next_stage_name accordingly
                                    try:
                                        last_stage_idx = effective_stage_order.index(last_stage)
                                        next_stage_name = effective_stage_order[last_stage_idx + 1]
                                        user_field = stage_to_user_attr_map.get(next_stage_name)
                                    except (ValueError, IndexError):
                                        # fallback: use original next_stage_name and user_field if error occurs
                                        pass
                            else:
                                # If conditions not met, fallback to your original DUAL_ROLE_OVERRIDES logic
                                for role in user_roles:
                                    override_key = (last_stage, role)
                                    if override_key in DUAL_ROLE_OVERRIDES:
                                        user_field = DUAL_ROLE_OVERRIDES[override_key]
                                        break
                        # Handle special cases for negotiation and DPO stages
                        if last_stage == 'stage8' and last_status == 'negotiation':
                            next_stage_name = 'stage5'
                            user_field = stage_to_user_attr_map.get(next_stage_name)
                        elif last_stage == 'stage9' and last_status == 'dpo':
                            next_stage_name = 'stage4'
                            user_field = stage_to_user_attr_map.get(next_stage_name)

                        next_user = getattr(procurement, user_field, None) if user_field else None
                        # #print("nex-user", next_user.userreg)
                        next_user_info = {
                            'name': next_user.get_full_name() if next_user else 'N/A',
                            'emp_id': get_emp_id(next_user)
                        }

                        stages_with_status.append({
                            'stage': next_stage_name,
                            'status': 'pending',
                            'datetime': stages_with_status[-1]['datetime'],
                            'comment': '',
                            'next_user': next_user_info
                        })

            except ValueError:
                    pass
            

            
    # If no stages were processed, return early 
    # Prepare the full data payload

    data = {
        'procurement_id': str(procurement.procurement_id),
        'stages_with_status': stages_with_status,
        'created_datetime': created_datetime,
        'users': {
            'user': {
                'name': procurement.user.get_full_name() if procurement.user else 'N/A',
                'emp_id': get_emp_id(procurement.user) if procurement.user else 'N/A',
            },
            'ra_user': {
                'name': procurement.ra_user.get_full_name() if procurement.ra_user else 'N/A',
                'emp_id': get_emp_id(procurement.ra_user) if procurement.ra_user else 'N/A',
            },
            'imm_user': {
                'name': procurement.imm_user.get_full_name() if procurement.imm_user else 'N/A',
                'emp_id': get_emp_id(procurement.imm_user)  if procurement.imm_user else 'N/A',
            },
            'account_user': {
                'name': procurement.account_user.get_full_name() if procurement.account_user else 'N/A',
                'emp_id': get_emp_id(procurement.account_user)  if procurement.account_user else 'N/A',
            },
            'aa_user': {
                'name': procurement.aa_user.get_full_name() if procurement.aa_user else 'N/A',
                'emp_id': get_emp_id(procurement.aa_user) if procurement.aa_user else 'N/A',
            },
        }
    }
    #print(data)
   
    # Send update to each user's group
    channel_layer = get_channel_layer()
    ist = pytz.timezone('Asia/Kolkata')
    created_datetime = procurement.datetime.astimezone(ist).strftime('%d-%m-%Y %H:%M:%S')

    for user in users:
        group_name =  f'tracking_{user.id}'
        message = {
            "type": "send_initial_data",
            "data": {
               'procurement_id': str(procurement.procurement_id),
                'action': 'update',
                'datetime': created_datetime,
                'data': data
            },
        }
        # #print(f"Sending to group: {group_name}")
        # #print(f"Message: {message}")
        async_to_sync(channel_layer.group_send)(group_name, message)  # ✅ Move inside the loop
 


@receiver(post_save, sender=StageProgress)
def send_stage_progress_update(sender, instance, created, **kwargs):
    try:
        procurement = instance.procurement_id
        if procurement.is_draft:
            return

        # Recalculate action_performed flag for the procurement
        last_remark = StageProgress.objects.filter(
            procurement_id__procurement_id=procurement.procurement_id
        ).values("stagename__stage", "remarktype").last()

        if last_remark and last_remark["stagename__stage"] == "stage1" and last_remark["remarktype"] in ["PR_Raised", "Approval", "Modified"]:
            procurement.action_performed = True
        else:
            procurement.action_performed = False
        
        # procurement.save()

        # Prepare data payload to send over websocket
        data = {
            "procurement_id": procurement.procurement_id,
            "stage": instance.stagename.stage,
            "procurement_idd":procurement.id,
            "remarktype": instance.remarktype,
            "datetime": str(instance.datetime),
            # "datetime":instance.datetime.isoformat(),
            'procurement_title': procurement.procurement_title,
            "action_performed": procurement.action_performed,
        }
        #print('data',data)
        #print('bufdget=======',procurement.budget)
        # Identify the RA user to send the update to
        ra_user = procurement.ra_user
        if ra_user:
            group_name = f"receive_ra_user_{ra_user.id}"
            #print('group_nqme',group_name)
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "send_procurement_update",
                    "data": data,
                }
            )

    except Exception as e:
        print(f"WebSocket send error: {e}")

@receiver(post_save, sender=StageProgress)
def send_reject_ra_procurement_update(sender, instance, created, **kwargs):
    try:
        procurement = instance.procurement_id  # FK to Procurement

        # Recalculate action_performed flag for stage2 reject scenario
        last_remark = StageProgress.objects.filter(
            procurement_id__procurement_id=procurement.procurement_id
        ).values("rejectstage__stage", "remarktype").last()

        if last_remark and last_remark["rejectstage__stage"] == "stage2" and last_remark["remarktype"] in ["Reject", "Modified"]:
            procurement.action_performed = True
        else:
            procurement.action_performed = False
        # procurement.save()

        # Prepare data payload for WebSocket
        data = {
            "procurement_id": procurement.procurement_id,
            "stage": instance.rejectstage.stage if instance.rejectstage else None,
            "remarktype": instance.remarktype,
            "procurement_title":procurement.procurement_title,
            "datetime": str(instance.datetime),
            "action_performed": procurement.action_performed,
            "procurement_idd":procurement.id,
        }

        # Identify RA user and send update over channel layer group
        ra_user = procurement.ra_user
        if ra_user:
            group_name = f"reject_ra_user_{ra_user.id}"
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "send_procurement_ra",
                    "data": data,
                }
            )

    except Exception as e:
        print(f"WebSocket send error in send_reject_ra_procurement_update: {e}")


@receiver(post_save, sender=StageProgress)
def send_aa_procurement_update(sender, instance, created, **kwargs):
    try:
        procurement = instance.procurement_id  # FK to Procurement
        if not procurement:
            return

        # Check if the update is relevant for AA
        stage = instance.stagename.stage if instance.stagename else None
        remark = instance.remarktype

        if stage not in ["stage4", "stage8"] or remark not in ["Approval", "Negotiation"]:
            return  # Not relevant for AA user

        # Update action_performed flag
        last_remark = StageProgress.objects.filter(
            procurement_id=procurement
        ).values("stagename__stage", "remarktype").last()

        if last_remark and last_remark["stagename__stage"] in ["stage4", "stage8"] and last_remark["remarktype"] in ["Approval", "Negotiation"]:
            procurement.action_performed = True
        else:
            procurement.action_performed = False
        # procurement.save()

        # Collect additional remark statuses
        reject_remarks = StageProgress.objects.filter(
            procurement_id__procurement_id=procurement.procurement_id,
            remarktype="Reject"
        ).values_list("remarktype", flat=True).distinct()

        approval_remarks = StageProgress.objects.filter(
            procurement_id__procurement_id=procurement.procurement_id,
            stagename__stage="stage5",
            remarktype="Approval"
        ).values_list("remarktype", flat=True).distinct()

        modified_remarks = StageProgress.objects.filter(
            procurement_id__procurement_id=procurement.procurement_id,
            remarktype="Modified"
        ).values_list("remarktype", flat=True).distinct()

        remarks = list(set(reject_remarks).union(approval_remarks, modified_remarks))

        # Prepare WebSocket data
        data = {
            "procurement_id": procurement.procurement_id,
            "stage": stage,
            "procurement_title":procurement.procurement_title,
            "procurement_idd":procurement.id,
            "remarktype": remark,
            "datetime": str(instance.datetime),
            "action_performed": procurement.action_performed,
            "statuses": remarks,
        }

        # Send update to AA user group
        aa_user = procurement.aa_user
        if aa_user:
            group_name = f"aa_user_{aa_user.id}"
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "send_procurement_aa",
                    "data": data,
                }
            )

    except Exception as e:
        print(f"WebSocket send error in send_aa_procurement_update: {e}")

@receiver(post_save, sender=StageProgress)
def send_indentor_procurement_update(sender, instance, created, **kwargs):
    try:
        #print("inside signal", instance)
        procurement = instance.procurement_id  # FK to Procurement
        if not procurement or not procurement.user:
            return

        indentor_user = procurement.user

        # Check if the update is relevant for Indentor
        stage = instance.stagename.stage if instance.stagename else None
        remark = instance.remarktype

        if stage not in ["stage1", "stage7"] or remark not in ["PR_Raised", "CST", "Modified"]:
            return  # Not relevant for Indentor

        # Update action_performed flag
        last_remark = StageProgress.objects.filter(
            procurement_id=procurement
        ).values("stagename__stage", "remarktype").last()

        if last_remark and last_remark["stagename__stage"] in ["stage1", "stage7"] and last_remark["remarktype"] in ["PR_Raised", "CST", "Modified"]:
            procurement.action_performed = True
        else:
            procurement.action_performed = False
        # procurement.save()

        # Collect additional remark statuses
        reject_remarks = StageProgress.objects.filter(
            procurement_id__procurement_id=procurement.procurement_id,
            remarktype="Reject"
        ).values_list("remarktype", flat=True).distinct()

        approval_remarks = StageProgress.objects.filter(
            procurement_id__procurement_id=procurement.procurement_id,
            stagename__stage="stage2",
            remarktype="Approval"
        ).values_list("remarktype", flat=True).distinct()

        modified_remarks = StageProgress.objects.filter(
            procurement_id__procurement_id=procurement.procurement_id,
            remarktype="Modified"
        ).values_list("remarktype", flat=True).distinct()

        remarks = list(set(reject_remarks).union(approval_remarks, modified_remarks))

        # Prepare WebSocket data
        data = {
            "procurement_id": procurement.procurement_id,
            "procurement_idd": procurement.id,
            "procurement_title":procurement.procurement_title,
            "stage": stage,
            "remarktype": remark,
            "datetime": str(instance.datetime),
            "action_performed": procurement.action_performed,
            "statuses": remarks,
        }

        # Send update to Indentor user group
        group_name = f"indentor_user_{indentor_user.id}"
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_procurement_indentor",
                "data": data,
            }
        )

    except Exception as e:
        print(f"WebSocket send error in send_indentor_procurement_update: {e}")


# @receiver(post_save, sender=StageProgress)
# def send_enquiry_procurement_update(sender, instance, created, **kwargs):
#     try:
#         if not created:
#             return

#         procurement = instance.procurement_id
#         if not procurement or not procurement.imm_user:
#             return

#         imm_user = procurement.imm_user
#         stage = instance.stagename.stage if instance.stagename else None
#         remark = instance.remarktype

#         if stage != "stage5" or remark != "Approval":
#             return

#         if procurement.is_delivered:
#             return
#         last_remark = StageProgress.objects.filter(
#             procurement_id=procurement
#         ).values("stagename__stage", "remarktype").last()

#         procurement.action_performed = (
#             last_remark and last_remark["stagename__stage"] == "stage5" and last_remark["remarktype"] == "Approval"
#         )
#         # procurement.save()

#         reject_remarks = StageProgress.objects.filter(
#             procurement_id__procurement_id=procurement.procurement_id,
#             remarktype="Reject"
#         ).values_list("remarktype", flat=True).distinct()

#         approval_remarks = StageProgress.objects.filter(
#             procurement_id__procurement_id=procurement.procurement_id,
#             stagename__stage="stage5",
#             remarktype="Approval"
#         ).values_list("remarktype", flat=True).distinct()

#         modified_remarks = StageProgress.objects.filter(
#             procurement_id__procurement_id=procurement.procurement_id,
#             remarktype="Modified"
#         ).values_list("remarktype", flat=True).distinct()

#         remarks = list(set(reject_remarks).union(approval_remarks, modified_remarks))

#         data = {
#             "procurement_id": procurement.procurement_id,
#             "procurement_idd": procurement.id,
#             "procurement_title":procurement.procurement_title,
#             "stage": stage,
#             "remarktype": remark,
#             "datetime": str(instance.datetime),
#             "action_performed": procurement.action_performed,
#             "statuses": remarks,
#             "imm_user": {
#                 "id": imm_user.id,
#                 "username": imm_user.username,
#                 "email": imm_user.email,
#                 "first_name": imm_user.first_name,
#                 "last_name": imm_user.last_name,
#                 # Add any other fields you want to send
#             },
#         }

#         group_name = f"enquiry_user_{imm_user.id}"
#         #print(f"📢 Sending to WebSocket group {group_name}: {data}")
#         channel_layer = get_channel_layer()
#         async_to_sync(channel_layer.group_send)(
#             group_name,
#             {
#                 "type": "send_procurement_enquiry",
#                 "data": data,
#             }
#         )

#     except Exception as e:
#         print(f"❌ WebSocket error in send_enquiry_procurement_update: {e}")
@receiver(post_save, sender=StageProgress)
def send_enquiry_procurement_update(sender, instance, created, **kwargs):
    try:
        if not created:
            return

        procurement = instance.procurement_id
        if not procurement or not procurement.imm_user:
            return

        imm_user = procurement.imm_user
        stage = instance.stagename.stage if instance.stagename else None
        remark = instance.remarktype

        # Must be stage5 approval
        if stage != "stage5" or remark != "Approval":
            return

        # --------------------------
        # ✔ APPLY YOUR REQUIRED CONDITION
        # --------------------------
        from django.db.models import OuterRef, Subquery

        latest_subquery = ModifiedPr.objects.filter(
            procurement_id=OuterRef('procurement_id')
        ).order_by('-datetime')

        latest_per_proc = ModifiedPr.objects.filter(
            procurement_id=procurement.id,
            id=Subquery(latest_subquery.values('id')[:1])
        ).first()

        condition_passed = False

        if latest_per_proc:
            # Case 1: ModifiedPR exists
            if (not latest_per_proc.modifiedpr.is_delivered and
                latest_per_proc.modifiedpr.pr_events == "Purchase_order"):
                condition_passed = True
        else:
            # Case 2: No ModifiedPR exists
            if (not procurement.is_delivered and
                procurement.pr_events == "Purchase_order"):
                condition_passed = True

        # ❌ If condition fails → exit (do not send websocket)
        if not condition_passed:
            return

        # --------------------------
        # Continue with your existing logic
        # --------------------------

        last_remark = StageProgress.objects.filter(
            procurement_id=procurement
        ).values("stagename__stage", "remarktype").last()

        procurement.action_performed = (
            last_remark and last_remark["stagename__stage"] == "stage5" and last_remark["remarktype"] == "Approval"
        )

        reject_remarks = StageProgress.objects.filter(
            procurement_id__procurement_id=procurement.procurement_id,
            remarktype="Reject"
        ).values_list("remarktype", flat=True).distinct()

        approval_remarks = StageProgress.objects.filter(
            procurement_id__procurement_id=procurement.procurement_id,
            stagename__stage="stage5",
            remarktype="Approval"
        ).values_list("remarktype", flat=True).distinct()

        modified_remarks = StageProgress.objects.filter(
            procurement_id__procurement_id=procurement.procurement_id,
            remarktype="Modified"
        ).values_list("remarktype", flat=True).distinct()

        remarks = list(set(reject_remarks).union(approval_remarks, modified_remarks))

        data = {
            "procurement_id": procurement.procurement_id,
            "procurement_idd": procurement.id,
            "procurement_title": procurement.procurement_title,
            "stage": stage,
            "remarktype": remark,
            "datetime": str(instance.datetime),
            "action_performed": procurement.action_performed,
            "statuses": remarks,
            "imm_user": {
                "id": imm_user.id,
                "username": imm_user.username,
                "email": imm_user.email,
                "first_name": imm_user.first_name,
                "last_name": imm_user.last_name,
            },
        }

        group_name = f"enquiry_user_{imm_user.id}"
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_procurement_enquiry",
                "data": data,
            }
        )

    except Exception as e:
        print(f"❌ WebSocket error in send_enquiry_procurement_update: {e}")



@receiver(post_save, sender=StageProgress)
def send_indentor_rejected_procurement(sender, instance, created, **kwargs):
    try:
        procurement = instance.procurement_id

        if (
            instance.remarktype == "Reject"
            and instance.rejectstage
            and instance.rejectstage.stage == "stage1"
            and instance.stagename.stage in ["stage2", "stage3", "stage4", "stage5"]
        ):
            last_remark = StageProgress.objects.filter(
                procurement_id__procurement_id=procurement.procurement_id
            ).values("stagename__stage", "remarktype").last()

            if last_remark and last_remark["remarktype"] == "Reject" and last_remark["stagename__stage"] <= "stage5":
                procurement.action_performed = True
            else:
                procurement.action_performed = False
            # procurement.save()

            data = {
                "procurement_id": procurement.procurement_id,
                "procurement_idd": procurement.id,
                "procurement_title":procurement.procurement_title,
                "stage": instance.stagename.stage,
                "remarktype": instance.remarktype,
                "datetime": str(instance.datetime),
                "action_performed": procurement.action_performed,
            }

            indentor_user = procurement.user  # Use the user field as indentor
            if indentor_user:
                group_name = f"rejected_indentor_user_{indentor_user.id}"
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        "type": "send_procurement_indentor_reject",
                        "data": data,
                    }
                )

    except Exception as e:
        print(f"[Signal Error] send_indentor_rejected_procurement: {e}")


# @receiver(post_save, sender=StageProgress)
# def send_enquiry_procurement_update(sender, instance, created, **kwargs):
#     try:
#         procurement = instance.procurement_id  # FK to Procurement
#         if not procurement or not procurement.imm_user:
#             return

#         imm_user = procurement.imm_user

#         # Check if relevant for IMM view: stage5 + Approval
#         stage = instance.stagename.stage if instance.stagename else None
#         remark = instance.remarktype

#         if stage != "stage5" or remark != "Approval":
#             return  # Not relevant for IMM

#         # Check last remark
#         last_remark = StageProgress.objects.filter(
#             procurement_id=procurement
#         ).values("stagename__stage", "remarktype").last()

#         if last_remark and last_remark["stagename__stage"] == "stage5" and last_remark["remarktype"] == "Approval":
#             procurement.action_performed = True
#         else:
#             procurement.action_performed = False
#         procurement.save()

#         # WebSocket data payload
#         data = {
#             "procurement_id": procurement.procurement_id,
#             "procurement_idd": procurement.id,
#             "stage": stage,
#             "remarktype": remark,
#             "datetime": str(instance.datetime),
#             "action_performed": procurement.action_performed,
#         }

#         # Send to IMM group
#         group_name = f"enquiry_user_{imm_user.id}"
#         channel_layer = get_channel_layer()

#         async_to_sync(channel_layer.group_send)(
#             group_name,
#             {
#                 "type": "send_procurement_enquiry",
#                 "data": data,
#             }
#         )

#     except Exception as e:
#         #print(f"WebSocket send error in send_imm_procurement_update: {e}")||||||| .r905


@receiver([post_save, post_delete], sender=BudgetAllocation)
@receiver([post_save, post_delete], sender=Purchase_Order)
def send_aa_budget_update(sender, instance, **kwargs):
    """
        Django signal receiver that listens for both post_save and post_delete events on the BudgetAllocation model,
        to update the budget page with real-time data
    """

    # Get the channel layer for WebSocket communication
    layer = get_channel_layer()

    # Retrieve all users with the "Accounts" role
    aa_users = UserReg.objects.filter(role__role="Approving Authority").select_related("user")

    # If no Accounts users exist, exit early (no one to notify)
    if not aa_users.exists():
        return

    # Use the first Accounts user to generate a common dashboard context
    # This assumes dashboard data is the same for all Accounts users
    dummy_user = aa_users.first().user

    # Generate the dashboard data for Accounts users
    context_data = get_aa_budget_data(dummy_user)

    # Loop through each Accounts user and send the data to their WebSocket group
    for aa_user in aa_users:
        
        # WebSocket group for the user
        group_name = f"budget_aa_user_{aa_user.user.id}" 

        # Send the context data to the group using Django Channels
        async_to_sync(layer.group_send)(
            group_name,
            {
                "type": "send_aa_budget_update",  # This must match the method in the consumer
                "data": context_data                  # Dashboard data payload
            }
        )





def get_accounts_pages_for_update(instance):
    if instance.remarktype == 'Reject':
        return ['rejectedaccounts']
    return ['accounts']

@receiver([post_save, post_delete], sender=StageProgress)
def notify_accounts_sidebar_users(sender, instance, **kwargs):
    procurement = instance.procurement_id
    account_user = procurement.account_user
    if not account_user:
        return

    channel_layer = get_channel_layer()
    pages = get_accounts_pages_for_update(instance)

    is_forwarded_to_account_user = (
        instance.forwarded_to and instance.forwarded_to.id == account_user.id
    )
    is_rejected_to_account_user = (
        instance.rejectuser and instance.rejectuser.id == account_user.id
    )

    for page in pages:
        group_name = f"sidebar_acc_{page}_user_{account_user.id}"
        message = {
            "type": "send_sidebar_update",
            "data": {
                "update_type": "refresh_sidebar",
                "role": "acc",            # role for filtering frontend
                "page": page,             # page for filtering frontend
                "timestamp": localtime(procurement.datetime).isoformat(),
                "procurement_id": procurement.procurement_id,
                "procurement_title":procurement.procurement_title,
                "action_performed": instance.user and getattr(instance.user, 'role', None) == 'acc',
                "user_role": getattr(instance.user, 'role', None),
                "forwarded_to_role": getattr(instance.forwarded_to, 'role', None),
                "reject_to_role": getattr(instance.rejectuser, 'role', None),
                # ✅ Exact match check
                "forwarded_to_account_user": is_forwarded_to_account_user,
                "rejected_to_account_user": is_rejected_to_account_user,


                "statuses": getattr(procurement, 'statuses', []),                 # optional statuses
                
                
            },
        }
        #print(f"Sending to group: {group_name}")
        #print(f"Message: {message}")
        
        async_to_sync(channel_layer.group_send)(group_name, message)



def get_imm_pages_for_update(instance):
    if instance.remarktype == 'Reject':
        return ['rejectedimm']
 
   
    return ['imm'] 


@receiver([post_save, post_delete], sender=StageProgress)
def notify_imm_sidebar_users(sender, instance, **kwargs):
    procurement = instance.procurement_id
    imm_user = procurement.imm_user  # Assuming IMM user exists, replace with your actual IMM user field.
    if not imm_user:
        return

    channel_layer = get_channel_layer()
    pages = get_imm_pages_for_update(instance)

    is_forwarded_to_imm_user = (
        instance.forwarded_to and instance.forwarded_to.id == imm_user.id
    )
    is_rejected_to_imm_user = (
        instance.rejectuser and instance.rejectuser.id == imm_user.id
    )
    action_by_imm = getattr(instance.user, 'role', '') == 'imm'
    #print("Pages in sidebar: ", pages)
    for page in pages:
        group_name = f"sidebar_imm_{page}_user_{imm_user.id}"
        message = {
            "type": "send_sidebar_update",
            "data": {
                "update_type": "refresh_sidebar_imm",
                "role": "imm",  # Role for filtering frontend
                "page": page,  # Page for filtering frontend
                "timestamp": localtime(procurement.datetime).isoformat(),
                "procurement_id": procurement.procurement_id,
                "procurement_title":procurement.procurement_title,
                "action_performed": action_by_imm,
                "user_role": getattr(instance.user, 'role', None),
                "forwarded_to_role": getattr(instance.forwarded_to, 'role', None),
                "reject_to_role": getattr(instance.rejectuser, 'role', None),
                "forwarded_to_imm_user": is_forwarded_to_imm_user,
                "rejected_to_imm_user": is_rejected_to_imm_user,
                "statuses": getattr(procurement, 'statuses', []),
            },
        }
        #print(f"Sending to group - sidebar: {group_name}")
        #print(f"Message: {message}")
        
        async_to_sync(channel_layer.group_send)(group_name, message)


from django.db.models import Max

def get_immdpo_pages_for_update(instance):
    procurement = instance.procurement_id

    # Step 1: Get latest datetime for stage7
    stage7_latest = StageProgress.objects.filter(
        procurement_id=procurement,
        stagename__stage="stage7"
    ).aggregate(latest=Max("datetime"))['latest']

    if not stage7_latest:
        return ['imm']  # If no stage7, return 'imm' directly

    # Step 2: Get roles count for procurement.user
    try:
        procurement_user_roles = UserReg.objects.get(user=procurement.user).role.all()
        role_count = procurement_user_roles.count()
    except UserReg.DoesNotExist:
        role_count = 0

    # Step 3: Handle based on role count
    if role_count > 1:  # Multiple roles
        if procurement.is_negotiation:
            # Step 4: Stage5 approval required after stage7 for negotiation
            stage5_latest_approval = StageProgress.objects.filter(
                procurement_id=procurement,
                stagename__stage="stage5",
                remarktype="Approval"
            ).aggregate(latest=Max("datetime"))['latest']

            if not stage5_latest_approval or stage5_latest_approval <= stage7_latest:
                return ['imm']

            if procurement.RA_negotiation:
                stage5_count = StageProgress.objects.filter(
                    procurement_id=procurement,
                    stagename__stage="stage5",
                    remarktype="Approval"
                ).count()

                if stage5_count < 2:
                    return ['imm']

            return ['dpo']  # Valid for DPO

        else:
            # Step 5: No negotiation, require stage1 approval after stage7
            stage1_latest_approval = StageProgress.objects.filter(
                procurement_id=procurement,
                stagename__stage="stage1",
                remarktype="Approval"
            ).aggregate(latest=Max("datetime"))['latest']

            if not stage1_latest_approval or stage1_latest_approval <= stage7_latest:
                return ['imm']

            return ['dpo']  # Valid for DPO

    else:
        # Single role: Normal flow, require stage2 approval after stage7
        stage2_latest_approval = StageProgress.objects.filter(
            procurement_id=procurement,
            stagename__stage="stage2",
            remarktype="Approval"
        ).aggregate(latest=Max("datetime"))['latest']

        if not stage2_latest_approval or stage2_latest_approval <= stage7_latest:
            return ['imm']

        # RA_negotiation check
        if procurement.RA_negotiation:
            stage5_count = StageProgress.objects.filter(
                procurement_id=procurement,
                stagename__stage="stage5",
                remarktype="Approval"
            ).count()

            if stage5_count >= 2:
                return ['dpo']
        else:
            return ['dpo']  # No negotiation, just return 'dpo'

    return ['imm']  # Default fallback if no conditions are met



@receiver([post_save, post_delete], sender=StageProgress)
def notify_immdpo_sidebar_users(sender, instance, **kwargs):
    procurement = instance.procurement_id
    imm_user = procurement.imm_user  # Assuming IMM user exists, replace with your actual IMM user field.
    if not imm_user:
        return

    channel_layer = get_channel_layer()
    pages = get_immdpo_pages_for_update(instance)

    is_forwarded_to_imm_user = (
        instance.forwarded_to and instance.forwarded_to.id == imm_user.id
    )
    action_by_imm = getattr(instance.user, 'role', '') == 'imm'
    role = 'imm'
    #print("Pages in sidebar-dpo: ", pages)
    for page in pages:
        group_name =  f"sidebar_{role}_{page}_user_{imm_user.id}"
        message = {
            "type": "send_sidebar_update",
            "data": {
                "update_type": "refresh_sidebar_dpo",
                "role": "imm",  # Role for filtering frontend
                "page": page,  # Page for filtering frontend
                "timestamp": localtime(procurement.datetime).isoformat(),
                "procurement_id": procurement.procurement_id,
                "procurement_title":procurement.procurement_title,
                "action_performed": action_by_imm,
                "user_role": getattr(instance.user, 'role', None),
                "forwarded_to_role": getattr(instance.forwarded_to, 'role', None),
                "forwarded_to_imm_user": is_forwarded_to_imm_user,
                "statuses": getattr(procurement, 'statuses', []),
            },
        }
        #print(f"Sending to group- dpo: {group_name}")
        #print(f"Message: {message}")
        
        async_to_sync(channel_layer.group_send)(group_name, message)

from django.db.models import Max, Q

def get_immneg_pages_for_update(instance):
    procurement = instance.procurement_id

    # Get the latest 'stage7' with 'CST'
    stage7_qs = StageProgress.objects.filter(
        procurement_id=procurement,
        stagename__stage="stage7",
        remarktype="CST"
    )

    # Check if there are any 'stage7' records with 'CST'
    if not stage7_qs.exists():
        return ['imm']

    # Check RA_negotiation flag (if not set, return 'imm')
  

    # Check if the user has the necessary roles
    raised_user = procurement.user
    #print("here", raised_user)
    if not raised_user:
        return ['imm']  # If no user, return 'imm'

    try:
        raised_user_reg = UserReg.objects.get(user=raised_user)
        raised_user_roles = [r.role for r in raised_user_reg.role.all()]
    except UserReg.DoesNotExist:
        return ['imm']  # If no user registration, return 'imm'
    #print("here", raised_user)
    #print(raised_user_roles)
    # If the user has exactly one role and RA_negotiation is true
    if len(raised_user_roles) == 1 and procurement.RA_negotiation:
        # Count Stage 2 Approvals for the procurement
        stage2_approvals_count = StageProgress.objects.filter(
            procurement_id=procurement,
            stagename__stage="stage2",
            remarktype="Approval"
        ).count()
        #print('hello',len(raised_user_roles))
        # Need at least 2 approvals to proceed to 'negotiation'
        if stage2_approvals_count >= 2:
            return ['negotiation']
    
    # If the user has more than one role and is already in negotiation
    elif len(raised_user_roles) > 1 and procurement.is_negotiation:
        return ['negotiation']
    #print('hi',len(raised_user_roles))
    # Default return if none of the above conditions are met
    return ['imm']


@receiver([post_save, post_delete], sender=StageProgress)
def notify_immneg_sidebar_users(sender, instance, **kwargs):
    procurement = instance.procurement_id
    imm_user = procurement.imm_user  # Assuming IMM user exists, replace with your actual IMM user field.
    if not imm_user:
        return

    channel_layer = get_channel_layer()
    pages = get_immneg_pages_for_update(instance)
    #print("pages: ", pages)

    is_forwarded_to_imm_user = (
        instance.forwarded_to and instance.forwarded_to.id == imm_user.id
    )
    action_by_imm = getattr(instance.user, 'role', '') == 'imm'
    role = 'imm'
    #print("Pages in sidebar-neg: ", pages)
    for page in pages:
        group_name =  f"sidebar_{role}_{page}_user_{imm_user.id}"
        message = {
            "type": "send_sidebar_update",
            "data": {
                "update_type": "refresh_sidebar_neg",
                "role": "imm",  # Role for filtering frontend
                "page": page,  # Page for filtering frontend
                "timestamp": localtime(procurement.datetime).isoformat(),
                "procurement_id": procurement.procurement_id,
                "procurement_title":procurement.procurement_title,
                "action_performed": action_by_imm,
                "user_role": getattr(instance.user, 'role', None),
                "forwarded_to_role": getattr(instance.forwarded_to, 'role', None),
                "forwarded_to_imm_user": is_forwarded_to_imm_user,
                "statuses": getattr(procurement, 'statuses', []),
            },
        }
        #print(f"Sending to group: {group_name}")
        #print(f"Message: {message}")
        
        async_to_sync(channel_layer.group_send)(group_name, message)







def get_immpo_pages_for_update(instance):
    procurement = instance.procurement_id

    try:
        # Step 1: Get DPO datetime for the current procurement
        dpo_entry = StageProgress.objects.filter(
            procurement_id=procurement,
            stagename__stage="stage9",
            remarktype="DPO"
        ).order_by('-datetime').first()

        if not dpo_entry:
            return []  # No DPO means no IMM PO page

        dpo_time = dpo_entry.datetime

        # Step 2: Check Stage 5 & Stage 4 approvals after DPO datetime
        stage5_approvals = StageProgress.objects.filter(
            procurement_id=procurement,
            stagename__stage="stage5",
            remarktype__in=["Approval", "Modified"],
            datetime__gt=dpo_time
        ).count()

        stage4_approvals = StageProgress.objects.filter(
            procurement_id=procurement,
            stagename__stage="stage4",
            remarktype__in=["Approval", "Modified"],
            datetime__gt=dpo_time
        ).count()

        # Step 3: Validate conditions for IMM PO page
        if stage5_approvals in [1, 2] and stage4_approvals in [1, 2]:
            # Optional check for whether a PO exists
            dpo = DPO.objects.filter(procurement=procurement).first()
            if dpo and dpo.poid:
                return ['po']

    except Exception as e:
        print("Signal check failed:", e)

    return []  # Default fallback if any condition fails

@receiver([post_save, post_delete], sender=StageProgress)
def notify_immpo_sidebar_users(sender, instance, **kwargs):
    procurement = instance.procurement_id
    imm_user = procurement.imm_user  # Assuming IMM user exists, replace with your actual IMM user field.
    if not imm_user:
        return

    channel_layer = get_channel_layer()
    pages = get_immpo_pages_for_update(instance)

    is_forwarded_to_imm_user = (
        instance.forwarded_to and instance.forwarded_to.id == imm_user.id
    )
    action_by_imm = getattr(instance.user, 'role', '') == 'imm'
    role = 'imm'
    #print("Pages in sidebar-po: ", pages)
    for page in pages:
        group_name =  f"sidebar_{role}_{page}_user_{imm_user.id}"
        message = {
            "type": "send_sidebar_update",
            "data": {
                "update_type": "refresh_sidebar_po",
                "role": "imm",  # Role for filtering frontend
                "page": page,  # Page for filtering frontend
                "timestamp": localtime(procurement.datetime).isoformat(),
                "procurement_id": procurement.procurement_id,
                "procurement_title":procurement.procurement_title,
                "action_performed": action_by_imm,
                "user_role": getattr(instance.user, 'role', None),
                "forwarded_to_role": getattr(instance.forwarded_to, 'role', None),
                "forwarded_to_imm_user": is_forwarded_to_imm_user,
                "statuses": getattr(procurement, 'statuses', []),
            },
        }
        #print(f"Sending to group- po: {group_name}")
        #print(f"Message: {message}")
        
        async_to_sync(channel_layer.group_send)(group_name, message)
