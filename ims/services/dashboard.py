
# services/dashboard.py
from calendar import month_name
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal
import json
import pdb
import re

from django.http import JsonResponse
from ims.models import BudgetAllocation,  Procurement, Project, Purchase_Order, PurchaseVendor, StageProgress, Stages, QuotationParticular, Negotiation, Particular, DPO, VendorQuotationDetails, DPO, Purchase_Order, POApproval,Vendor, CompartiveStatementPR
from django.db.models import OuterRef, Subquery, Max, Sum, Q, F, Count, FloatField, ExpressionWrapper, Avg
from django.db.models.functions import Cast
from dateutil.relativedelta import relativedelta
from django.db.models import Prefetch

class DashboardDataHelper:
    """
    A utility class that gathers and summarizes dashboard-related data 
    for users involved in the procurement process (indentors, RAs, AAs).
    """

    def __init__(self, user, user_field, project_filter=None):
        # Initialize with the user, their related field in procurement, and optional project filter
        self.user = user
        self.user_field = user_field  # e.g., 'user', 'ra_user', 'aa_user'
        self.project_filter = project_filter

    def get_procurements(self):
   
            # Retrieve procurements associated with the user (optionally filtered by project)
            filter_kwargs = {
                self.user_field: self.user,
                'is_draft': False  # Ensure is_draft is False
            }
            if self.project_filter:
                filter_kwargs['project_id'] = self.project_filter
            return Procurement.objects.filter(**filter_kwargs)


    def get_user_projects(self):
    # Return a list of projects the user is involved in (distinct), where the related procurements are not drafts
        filter_kwargs = {
            f'procurement__{self.user_field}': self.user,
            'procurement__is_draft': False
        }
        return list(Project.objects.filter(**filter_kwargs).distinct().values('project_id', 'name'))


    def get_stage_annotations(self):
        # Annotate procurements with latest stage progress details using subqueries
        latest_stage = StageProgress.objects.filter(procurement_id=OuterRef('pk')).order_by('-datetime')
        return {
            'latest_stage_name': Subquery(latest_stage.values('stagename__stage')[:1]),
            'latest_stage_remarktype': Subquery(latest_stage.values('remarktype')[:1]),
            'latest_stage_user': Subquery(latest_stage.values('user__first_name')[:1]),
            'latest_stage_rejectuser_id': Subquery(latest_stage.values('rejectuser__id')[:1]),
            'latest_stage_rejectstage': Subquery(latest_stage.values('rejectstage__stage')[:1]),
        }

    def get_next_user_field(self, remarktype, current_stage):
        # Determine the next stage or remark label based on current stage and remark type
        mapping = {
            ('PR_Raised', 'stage1'): 'PR Raised',
            ('Approval', 'stage1'): 'Recommended',
            ('Approval', 'stage2'): 'Recommended',
            ('Approval', 'stage3'): 'Recommended',
            ('Approval', 'stage4'): 'Recommended',
            ('Approval', 'stage5'): 'Recommended',
            ('Modified', 'stage1'): 'PR Modified',
        }
        return 'Returned' if remarktype == 'Reject' else mapping.get((remarktype, current_stage), None)

    # def get_data(self):
        
    #     # Fetch procurements with latest stage annotations
    #     procurements_qs = self.get_procurements().annotate(**self.get_stage_annotations())
        
    #     # Get projects the user is involved with
    #     projects_list = self.get_user_projects()

    #     # Mapping of internal stage codes to user-friendly names
    #     stage_name_mapping = {
    #         'stage1': 'Indentor',
    #         'stage2': 'Recommending Authority',
    #         'stage3': 'IMM',
    #         'stage4': 'Accounts',
    #         'stage5': 'Approving Authority',
    #         'stage6': 'enquiry_approval',
    #         'stage7': 'CST_approval',
    #         'stage8': 'Negotiation_approval',
    #         'stage9': 'DPO_approval',
    #         'stage10': 'PO',
    #     }

    #     # Build update logs for the dashboard
    #     updates = []
    #     for p in procurements_qs:
    #         stage = stage_name_mapping.get(p.latest_stage_name, p.latest_stage_name)
    #         next_remarktype = self.get_next_user_field(p.latest_stage_remarktype, p.latest_stage_name)
    #         updates.append({
    #             'procurement_id': p.id,
    #             'stage': stage,
    #             'remarktype': next_remarktype,
    #             'modified_pr': p.modifiedpr_id or 'No ID',
    #             'project_id': p.project.project_id if p.project else 'None',
    #             'project_name': p.project.name if p.project else 'No Project'
    #         })

    #     # Filter only original (non-modified) procurements
    #     original_procurements = procurements_qs.filter(modificationpr=False)
    #     original_procurement_ids = list(original_procurements.values_list('id', flat=True))
    #     total_procurements = len(original_procurement_ids)

    #     # Count approved procurements (ones that have POs)
    #     approved_ids = PurchaseOrder.objects.filter(
    #         procurement_id__in=original_procurement_ids
    #     ).values_list('procurement_id', flat=True).distinct()

    #     approved_count = Procurement.objects.filter(
    #         id__in=approved_ids,
    #         is_draft=False,
    #         modifiedpr_id__isnull=True
    #     ).filter(**{self.user_field: self.user}).count()

    #     # Get the Stage object for negotiation stage8
    #     negotiation_stage = Stages.objects.filter(stage='stage8').first()

    #     # Get the latest stage entry for each procurement
    #     latest_stages = StageProgress.objects.filter(
    #         procurement_id__in=original_procurement_ids
    #     ).values('procurement_id').annotate(latest_datetime=Max('datetime'))

    #     latest_map = {item['procurement_id']: item['latest_datetime'] for item in latest_stages}

    #     # Mapping of stages to remarktypes for filtering
    #     stage_remarktype_mapping = {
    #         'enquiry_approval': {'stage': 'stage6', 'remarktype': 'enquiry_approval'},
    #         'CST_approval': {'stage': 'stage7', 'remarktype': 'CST_approval'},
    #         'Negotiation_approval': {'stage': 'stage8', 'remarktype': 'Negotiation_approval'},
    #         'DPO_approval': {'stage': 'stage9', 'remarktype': 'DPO_approval'},
    #         # 'PO': {'stage': 'stage10', 'remarktype': 'PO'},
    #     }
    #     #import pdb; #pdb.set_trace
    #     # Query actual stage progress objects for latest stages
    #     stages_queryset = StageProgress.objects.filter(
    #         procurement_id__in=latest_map.keys(),
    #         datetime__in=latest_map.values()
    #     ).select_related('stagename')

    #     # Build stage_summary dynamically
    #     stage_summary = {}

    #     # ✅ Handle Negotiation_approval separately
    #     negotiation_approval_count = 0

    #     for procurement in original_procurements.prefetch_related('particular'):
    #         particular_ids = list(procurement.particular.values_list('id', flat=True))
    #         if not particular_ids:
    #             continue

    #         part_to_negotiation = {}

    #         for pid in particular_ids:
    #             qp = QuotationParticular.objects.filter(csparticular_id=pid).first()
    #             if not qp:
    #                 continue  # Skip this particular if no quotation
    #             nego = Negotiation.objects.filter(quoted_vendors=qp).first()
    #             if not nego:
    #                 continue  # Skip this particular if no negotiation
    #             part_to_negotiation[pid] = nego

    #         if not part_to_negotiation:
    #             continue  # No particular has negotiation; skip this procurement

    #         all_ok = True
    #         for nego in part_to_negotiation.values():
    #             latest_sp = (
    #                 StageProgress.objects
    #                 .filter(nego_quota_particular=nego)
    #                 .order_by('-datetime')
    #                 .first()
    #             )
    #             if not latest_sp:
    #                 all_ok = False
    #                 break
    #             if (
    #                 latest_sp.stagename.stage != 'stage8' or
    #                 latest_sp.remarktype != 'Negotiation_approval'
    #             ):
    #                 all_ok = False
    #                 break

    #         if all_ok:
    #             negotiation_approval_count += 1

    #     # ✅ Set negotiation_approval in stage_summary
    #     stage_summary['Negotiation_approval'] = negotiation_approval_count

    #     # ✅ Handle other stages normally using the pre-fetched queryset
    #     for key, value in stage_remarktype_mapping.items():
    #         if key == 'Negotiation_approval':
    #             continue  # Already handled above

    #         filtered_stages = [
    #             sp for sp in stages_queryset
    #             if sp.stagename.stage == value['stage'] and sp.remarktype == value['remarktype']
    #         ]
    #         stage_summary[key] = len(filtered_stages)

    #     # for key, value in stage_remarktype_mapping.items():
    #     #     filtered_stages = [
    #     #         sp for sp in stages_queryset
    #     #         if sp.stagename.stage == value['stage'] and sp.remarktype == value['remarktype']
    #     #     ]
    #     #     stage_summary[key] = len(filtered_stages)

    #     # Build procurement_stages list (optional, shows stage for all procurements)
    #     procurement_stage_map = {
    #         sp.procurement_id: stage_name_mapping.get(sp.stagename.stage, sp.stagename.stage)
    #         for sp in stages_queryset
    #     }

    #     procurement_stages = [
    #         {'procurement_id': pid, 'stage_name': procurement_stage_map.get(pid, 'N/A')}
    #         for pid in original_procurement_ids
    #     ]

    def get_data(self):
        # Fetch procurements with latest stage annotations
        procurements_qs = self.get_procurements().annotate(**self.get_stage_annotations())

        # Get projects the user is involved with
        projects_list = self.get_user_projects()

        # Stage name mapping for UI
        stage_name_mapping = {
            'stage1': 'Indentor',
            'stage2': 'Recommending Authority',
            'stage3': 'IMM',
            'stage4': 'Accounts',
            'stage5': 'Approving Authority',
            'stage6': 'enquiry_approval',
            'stage7': 'CST_approval',
            'stage8': 'Negotiation_approval',
            'stage9': 'DPO_approval',
            'stage10': 'PO',
        }

        # Dashboard updates log
        updates = []
        for p in procurements_qs:
            stage = stage_name_mapping.get(p.latest_stage_name, p.latest_stage_name)
            next_remarktype = self.get_next_user_field(p.latest_stage_remarktype, p.latest_stage_name)
            updates.append({
                'procurement_id': p.procurement_id,
                'stage': stage,
                'remarktype': next_remarktype,
                'modified_pr': p.modifiedpr_id or 'No ID',
                'project_id': p.project.project_id if p.project else 'None',
                'project_name': p.project.name if p.project else 'No Project'
            })


        # Original procurements only (not modified)
        original_procurements = procurements_qs.filter(modificationpr=False)
        original_procurement_ids = list(original_procurements.values_list('id', flat=True))
        total_procurements = len(original_procurement_ids)

        # Count approved procurements (those with a PurchaseOrder)
        approved_ids = Purchase_Order.objects.filter(
            procurement_id__in=original_procurement_ids
        ).values_list('procurement_id', flat=True).distinct()

        approved_count = Procurement.objects.filter(
            id__in=approved_ids,
            is_draft=False,
            modifiedpr_id__isnull=True
        ).filter(**{self.user_field: self.user}).count()

        # Mapping of stages to remark types for stage summary
        stage_remarktype_mapping = {
            'enquiry_approval': {'stage': 'stage6', 'remarktype': 'enquiry_approval'},
            'CST_approval': {'stage': 'stage7', 'remarktype': 'CST_approval'},
            'Negotiation_approval': {'stage': 'stage8', 'remarktype': 'Negotiation_approval'},
            'DPO_approval': {'stage': 'stage9', 'remarktype': 'DPO_approval'},
            'PO' : { 'stage': 'stage10', 'remarktype': 'PO'},
        }

        # Get latest StageProgress entries for each procurement
        latest_stages = StageProgress.objects.filter(
            procurement_id__in=original_procurement_ids
        ).values('procurement_id').annotate(latest_datetime=Max('datetime'))


        latest_map = {item['procurement_id']: item['latest_datetime'] for item in latest_stages}

        stages_queryset = StageProgress.objects.filter(
            procurement_id__in=latest_map.keys(),
            datetime__in=latest_map.values()
        ).select_related('stagename')
      
        stage_summary = {}
        negotiation_approval_count = 0
        negotiation_pr_particular_map = {} 

        #print("🔍 Pre-fetching related QuotationParticulars and Negotiations...")
        qp_map = {
            qp.csparticular_id: qp for qp in QuotationParticular.objects.filter(
                csparticular_id__in=Particular.objects.filter(
                    procurement__in=original_procurements
                ).values_list('id', flat=True)
            )
        }

        nego_map = {
            nego.quoted_vendors_id:  nego for nego in Negotiation.objects.filter(
                quoted_vendors__in=qp_map.values()
            )
        }

        #print(f"🔁 Loaded {len(qp_map)} QuotationParticulars and {len(nego_map)} Negotiations.")
        # --------------------------------------------------
        # ✅ FIXED: Build latest + previous StageProgress per negotiation
        # --------------------------------------------------

        # --------------------------------------------------
        # ✅ Build latest + previous StageProgress per negotiation
        # --------------------------------------------------

        stage_progress_qs = (
            StageProgress.objects
            .filter(nego_quota_particular__in=nego_map.values())
            .select_related("stagename")
            .order_by("nego_quota_particular_id", "-datetime")
        )

        # nego_id → [latest, previous]
        stage_progress_map = {}

        for sp in stage_progress_qs:
            key = sp.nego_quota_particular_id

            if key not in stage_progress_map:
                stage_progress_map[key] = []

            if len(stage_progress_map[key]) < 2:
                stage_progress_map[key].append(sp)


        # --------------------------------------------------
        # ✅ PROCUREMENT LEVEL NEGOTIATION APPROVAL CHECK
        # --------------------------------------------------
        negotiation_approval_count = 0
        negotiation_pr_particular_map = {}
        negotiation_approved_pr_ids = []
        neg_part_pair_list = []

        for procurement in original_procurements.prefetch_related("particular"):
            # ##pdb.set_trace()
            particular_ids = list(procurement.particular.values_list("id", flat=True))
            if not particular_ids:
                continue

            # 🔍 Filter only particulars which REQUIRE negotiation
            negotiation_required_pids = [
                pid for pid in particular_ids
                if qp_map.get(pid) and qp_map[pid].ra_negotiation
            ]

            if not negotiation_required_pids:
                # No negotiations → skip this procurement
                continue

            procurement_fully_approved = True
            approved_particulars = []

            for pid in negotiation_required_pids:
                qp = qp_map.get(pid)
                nego = nego_map.get(qp.id)

                
                if not nego:
                    procurement_fully_approved = False
                    break

                stages = stage_progress_map.get(nego.id, [])

                
                if len(stages) < 2:
                    procurement_fully_approved = False
                    break

                latest_sp, prev_sp = stages[0], stages[1]

                latest_stage = latest_sp.stagename.stage if latest_sp.stagename else None
                prev_stage = prev_sp.stagename.stage if prev_sp.stagename else None

                
                if latest_stage in ["stage9", "stage10"]:
                    procurement_fully_approved = False
                    break

                vendors_for_procurement = Vendor.objects.filter(
                    stageprogress__procurement_id=procurement
                ).distinct()

                stage9_vendors = Vendor.objects.filter(
                    stageprogress__procurement_id=procurement,
                    stageprogress__stagename__stage="stage9"
                ).distinct()

                if vendors_for_procurement.exists() and \
                stage9_vendors.count() == vendors_for_procurement.count():
                    procurement_fully_approved = False
                    break

                
                is_valid = (
                    latest_stage == "stage5" and
                    latest_sp.remarktype == "Approval" and
                    prev_stage == "stage8" and
                    prev_sp.remarktype == "Negotiation_approval"
                )

                if not is_valid:
                    procurement_fully_approved = False
                    break

                approved_particulars.append(pid)

            
            if procurement_fully_approved:
                pr_id = procurement.procurement_id

                negotiation_approval_count += 1
                negotiation_approved_pr_ids.append(pr_id)
                negotiation_pr_particular_map[pr_id] = approved_particulars

                for part_id in approved_particulars:
                    neg_part_pair_list.append({
                        "pr_id": pr_id,
                        "particular_id": part_id
                    })

        # Store in summary
        stage_summary["Negotiation_approval"] = {
            "count": negotiation_approval_count,
            "pr_particular_pairs": neg_part_pair_list,
            "pr_ids": negotiation_approved_pr_ids,
        }


        #import pdb; #pdb.set_trace
        # --- DPO Approval Logic ---
        # dpo_approval_count = 0
        # dpo_approved_pr_ids = []
        # dpo_vendor_pairs = []   # ⬅️ NEW
        
        # for procurement in original_procurements.prefetch_related('particular'):
        #     particular_ids = procurement.particular.values_list("id", flat=True)
            

        #     ra_vendor_ids = (
        #         VendorQuotationDetails.objects
        #         .filter(particular__csparticular_id__in=particular_ids, particular__ra_choosen_vendor=True)
        #         .values_list("sources__vendor_id", flat=True)
        #         .distinct()
        #     )

        #     ra_vendor_ids = set(ra_vendor_ids)

        #     if not ra_vendor_ids:
        #         continue

        #     approved_vendors = set()
            
        #     for vendor_id in ra_vendor_ids:
        #         latest_stage = StageProgress.objects.filter(
        #             procurement_id=procurement,
        #             vendors__vendor_id=vendor_id
        #         ).order_by('-datetime').first()

        #         if latest_stage and latest_stage.stagename.stage == "stage5" and latest_stage.remarktype == "Approval":
        #             approved_vendors.add(vendor_id)

        #     if len(approved_vendors) == len(ra_vendor_ids) and ra_vendor_ids:

        #         # Count the procurement
        #         dpo_approval_count += 1
        #         dpo_approved_pr_ids.append(procurement.procurement_id)

        #         # Save vendor pairs for frontend
        #         for v in approved_vendors:
        #             dpo_vendor_pairs.append({
        #                 "pr_id": procurement.procurement_id,
        #                 "vendor_id": v
        #             })

        # # Save in stage_summary
        # stage_summary['DPO_approval'] = {
        #     "count": dpo_approval_count,
        #     "pr_ids": dpo_approved_pr_ids,
        #     "vendor_pairs": dpo_vendor_pairs,   # ⬅️ NEW
        # }

        dpo_approval_count = 0
        dpo_approved_pr_ids = []
        dpo_vendor_pairs = []   # ⬅️ NEW

        for procurement in original_procurements.prefetch_related('particular'):
            particular_ids = procurement.particular.values_list("id", flat=True)

            # ------------------------------------------------------------
            # 🔹 EXISTING MULTI-VENDOR RA FLOW (unchanged)
            # ------------------------------------------------------------
            ra_vendor_ids = (
                VendorQuotationDetails.objects
                .filter(particular__csparticular_id__in=particular_ids, particular__ra_choosen_vendor=True)
                .values_list("sources__code", flat=True)
                .distinct()
            )

            ra_vendor_ids = set(ra_vendor_ids)

            if ra_vendor_ids:
                approved_vendors = set()

                for code in ra_vendor_ids:
                    latest_stage = StageProgress.objects.filter(
                        procurement_id=procurement,
                        vendors__code=code
                    ).order_by('-datetime').first()

                    if latest_stage and latest_stage.stagename.stage == "stage5" and latest_stage.remarktype == "Approval":
                        approved_vendors.add(code)

                if len(approved_vendors) == len(ra_vendor_ids):

                    dpo_approval_count += 1
                    dpo_approved_pr_ids.append(procurement.procurement_id)

                    for v in approved_vendors:
                        dpo_vendor_pairs.append({
                            "pr_id": procurement.procurement_id,
                            "code": v
                        })

                # Continue to next procurement — RA case handled
                continue

            # ------------------------------------------------------------
            # 🔹 NEW: SINGLE-VENDOR → DIRECT → DPO FLOW
            # ------------------------------------------------------------

            # STEP 1: Find all vendors for this PR
            # ##pdb.set_trace()
            all_vendor_ids = (
                VendorQuotationDetails.objects
                .filter(particular__csparticular_id__in=particular_ids)
                .values_list("sources__code", flat=True)
                .distinct()
            )
            all_vendor_ids = list(set(all_vendor_ids))

            # If not single vendor, skip
            if len(all_vendor_ids) != 1:
                continue

            vendor_id = all_vendor_ids[0]

            # STEP 2: Check if CST was approved AND sent to DPO
            # 1️⃣ CST approval check (StageProgress)
            cst_approved = StageProgress.objects.filter(
                procurement_id__procurement_id=procurement.procurement_id,
                stagename__stage="stage7",
                remarktype="CST_approval"
            ).exists()

            if not cst_approved:
                continue   # CST not approved → skip


            # 2️⃣ Get actual CST entry to check send_to value
            cst_entry = (
                CompartiveStatementPR.objects
                .filter(pro_id__procurement_id=procurement.procurement_id)
                .order_by("-csdate")
                .first()
            )

            # 3️⃣ Check if CST was sent directly to DPO
            if not cst_entry or cst_entry.send_to != "DPO":
                continue

            # STEP 3: Latest vendor stage must be stage5 Approval
            try:
                    
                latest_stage = (
                    StageProgress.objects
                    .filter(
                        procurement_id=procurement,
                        vendors__code=code
                    )
                    .order_by("-datetime")
                    .first()
                )
            except Exception as e:
                latest_stage = None

            if latest_stage and latest_stage.stagename.stage == "stage5" and latest_stage.remarktype == "Approval":

                dpo_approval_count += 1
                dpo_approved_pr_ids.append(procurement.procurement_id)

                dpo_vendor_pairs.append({
                    "pr_id": procurement.procurement_id,
                    "code": code
                })

        # ------------------------------------------------------------
        # SAVE IN SUMMARY
        # ------------------------------------------------------------
        stage_summary['DPO_approval'] = {
            "count": dpo_approval_count,
            "pr_ids": dpo_approved_pr_ids,
            "vendor_pairs": dpo_vendor_pairs,
        }




        #import pdb; #pdb.set_trace
        # --- PO Approval Logic (stage10) ---
        #print("\n🔍 Checking PO signatures for approval increment...")

        po_approval_count = 0
        po_approved_pr_ids = []
        po_vendor_list = []


        # Get all Purchase Orders related to the procurements being tracked
        purchase_orders = Purchase_Order.objects.filter(procurement_id__in=original_procurement_ids)

        for po in purchase_orders:

            # ✅ Directly count if po_sign is True
            if po.po_sign:
                po_approval_count += 1
                pr_id = po.procurement.procurement_id

                po_approved_pr_ids.append(pr_id)

                # Get vendor
                vendor = po.draft_po.sources if po.draft_po else None
                vendor_name = vendor.company_name1 if vendor else "Unknown Vendor"
                code = vendor.id if vendor else ''

                po_vendor_list.append({
                    "pr_id": pr_id,
                    "code": code,
                    "vendor_name": vendor_name,
                })

                continue


            # Otherwise, check POApproval table
            approvals = POApproval.objects.filter(po=po)

            if not approvals.exists():
                #print(f"⚠️ PO {po.id} has no assigned approvers — skipping.")
                continue

            # Check if all assigned users have signed
            all_signed = all(a.done_sign for a in approvals)

            if all_signed:
                po_approval_count += 1
                pr_id = po.procurement.procurement_id

                po_approved_pr_ids.append(pr_id)

                

                vendor = po.draft_po.sources
                vendor_name = vendor.company_name1 if vendor else "Unknown Vendor"
                code = vendor.id if vendor else ''

                po_vendor_list.append({
                    "pr_id": pr_id,
                    "code": code,
                    "vendor_name": vendor_name,
                })

            else:
                signed_count = sum(a.done_sign for a in approvals)
                total_approvers = approvals.count()
                #print(f"❌ PO {po.id} → Signatures incomplete ({signed_count}/{total_approvers}).")

        #print(f"\n📊 Total POs fully signed: {po_approval_count}")
        stage_summary['PO'] = {
            "count": po_approval_count,
            "pr_ids": po_approved_pr_ids,
            "vendors": po_vendor_list,
        }

        cst_valid_pr_ids = set()

        # Fetch all stages for relevant procurements
        all_stage_qs = StageProgress.objects.filter(
            procurement_id__in=original_procurement_ids
        ).select_related("stagename")

        # Map stages per procurement
        cst_stage_map = {}
        for sp in all_stage_qs:
            pid = sp.procurement_id
            cst_stage_map.setdefault(pid, []).append(sp)

        for pr_id, stages in cst_stage_map.items():
            stages_sorted = sorted(stages, key=lambda x: x.datetime)
            
            # Find latest Stage7 CST_approval
            stage7_cst_list = [sp for sp in stages_sorted if sp.stagename.stage == "stage7" and sp.remarktype == "CST_approval"]
            if not stage7_cst_list:
                continue  # No stage7 CST_approval
            
            latest_stage7_cst = stage7_cst_list[-1]
            latest_stage7_time = latest_stage7_cst.datetime

            cst_count = 1
            pr_invalid = False

            # Stages after latest Stage7 CST_approval
            for sp in stages_sorted:
                if sp.datetime <= latest_stage7_time:
                    continue  # Only consider stages after Stage7

                stage = sp.stagename.stage
                remark = sp.remarktype

                if stage == "stage1":
                    cst_count = 1  # Keep 1
                elif stage == "stage2" and remark == "Approval":
                    cst_count = 0  # Reset to 0
                elif stage =="stage1" and remark =="Reject":
                    cst_count =0

                elif stage == 'stage2' and remark == "Reject":
                    cst_count = 0

                else:
                    pr_invalid = True  # Any other stage invalidates the PR
                    break

            # Final decision: count must be 1 and not invalid
            if cst_count == 1 and not pr_invalid:
                # convert PR ID to string for JSON serialization
                cst_valid_pr_ids.add(str(pr_id))

        # Stage summary in exactly the format frontend expects
        stage_summary["CST_approval_new"] = {
            "count": len(cst_valid_pr_ids),
            "pr_ids": list(cst_valid_pr_ids),
        }
        print(stage_summary,'stage_summary')


        #import pdb; #pdb.set_trace
        # ✅ Handle other stages using pre-fetched queryset
        # for key, value in stage_remarktype_mapping.items():
        #     if key in ['Negotiation_approval', 'DPO_approval', 'PO']:
        #         continue  # Already handled
        #     filtered_stages = [
        #         sp for sp in stages_queryset
        #         if sp.stagename.stage == value['stage'] and sp.remarktype == value['remarktype']
        #     ]
        #     stage_summary[key] = {
        #         "count": len(filtered_stages),
        #         "pr_ids": list({sp.procurement_id.procurement_id for sp in filtered_stages})
        #     }


        # # Optional: Show latest stage name per procurement
        # procurement_stage_map = {
        #     sp.procurement_id: stage_name_mapping.get(sp.stagename.stage, sp.stagename.stage)
        #     for sp in stages_queryset
        # }

        # procurement_stages = [
        #     {'procurement_id': pid, 'stage_name': procurement_stage_map.get(pid, 'N/A')}
        #     for pid in original_procurement_ids
        # ]

       
        # # -----------------------
        # # 🔹 Filters for Purchase Orders
        # # -----------------------
        # filters = {
        #     "procurement__modifiedpr_id__isnull": True,
        #     f"procurement__{self.user_field}": self.user,
        # }


        # approved_pos = (
        #     Purchase_Order.objects
        #     .select_related("draft_po", "draft_po__sources")
        #     .filter(**filters)
        # )

        # if self.project_filter:
        #     approved_pos = approved_pos.filter(procurement__project_id=self.project_filter)

        # # -----------------------
        # # 🔹 Vendor performance aggregation
        # # -----------------------
        # # We'll aggregate based on vendor (draft_po.sources)
        # vendor_stats = (
        #     approved_pos
        #     .values(
        #         code=F("draft_po__sources__id"),
        #         vendor_name=F("draft_po__sources__company_name1"),
        #     )
        #     .annotate(
        #         procurement_count=Count("id"),  # How many POs per vendor
        #         total_committed_price=Sum(Cast("draft_po__grand_total", FloatField())),  # Sum of totals
        #         avg_delivery_days=Avg(
        #             Cast(
        #                 F("draft_po__delivery_weeks"),
        #                 output_field=FloatField()
        #             )
        #         )
        #     )
        # )

        # # -----------------------
        # # 🔹 Compute average delivery days (from text field like "2 weeks", etc.)
        # # -----------------------
        # vendor_data = {}

        # for po in approved_pos:
        #     if not po.draft_po or not po.draft_po.sources:
        #         continue

        #     vendor_obj = po.draft_po.sources
        #     vendor = vendor_obj.company_name1 or vendor_obj.vendor_name or "Unknown Vendor"

        #     delivery_str = (po.draft_po.delivery_weeks or "").strip().lower()
        #     delivery_days = 0
        #     match = re.match(r"(?i)\s*(\d+)\s*(day|days|week|weeks|month|months|year|years)", delivery_str)
        #     if match:
        #         val, unit = int(match.group(1)), match.group(2)
        #         if "day" in unit:
        #             delivery_days = val
        #         elif "week" in unit:
        #             delivery_days = val * 7
        #         elif "month" in unit:
        #             delivery_days = val * 30
        #         elif "year" in unit:
        #             delivery_days = val * 365

        #     vendor_data.setdefault(vendor, {"count": 0, "total": Decimal("0.00"), "delivery": 0, "entries": 0})
        #     vendor_data[vendor]["count"] += 1
        #     vendor_data[vendor]["total"] += Decimal(po.draft_po.grand_total or 0)
        #     vendor_data[vendor]["delivery"] += delivery_days
        #     vendor_data[vendor]["entries"] += 1

        # # -----------------------
        # # 🔹 Build final vendor summary
        # # -----------------------
        # vendor_summary = []
        # for v, d in vendor_data.items():
        #     avg_days = round(d["delivery"] / d["entries"], 1) if d["entries"] else 0
        #     vendor_summary.append({
        #         "vendor_name": v,
        #         "procurement_count": d["count"],
        #         "avg_delivery_days": avg_days,
        #         "total_committed_price": round(float(d["total"]), 2),
        #         "total_expenditure_price": 0,  # Placeholder (can fill later)
        #     })

        # # -----------------------
        # # 🔹 Pick top 5 vendors
        # # -----------------------
        # top_vendors = sorted(vendor_summary, key=lambda x: x["procurement_count"], reverse=True)[:5]

        # all_procurement_ids = list(original_procurements.values_list('procurement_id', flat=True))

        for key, value in stage_remarktype_mapping.items():
            if key in ['Negotiation_approval', 'DPO_approval', 'PO']:
                continue  # Already handled
            filtered_stages = [
                sp for sp in stages_queryset
                if sp.stagename.stage == value['stage'] and sp.remarktype == value['remarktype']
            ]
            stage_summary[key] = {
                "count": len(filtered_stages),
                "pr_ids": list({sp.procurement_id.procurement_id for sp in filtered_stages})
            }



        # Optional: map each procurement to its latest stage name for detailed list
        procurement_stage_map = {
            sp.procurement_id: stage_name_mapping.get(sp.stagename.stage, sp.stagename.stage)
            for sp in stages_queryset
        }

        procurement_stages = [
            {'procurement_id': pid, 'stage_name': procurement_stage_map.get(pid, 'N/A')}
            for pid in original_procurement_ids
        ]

       # Fetch all approved purchase orders
        approved_pos = Purchase_Order.objects.select_related(
            "draft_po", "draft_po__sources"
        ).filter(procurement__modifiedpr_id__isnull=True)

        if getattr(self, "project_filter", None):
            approved_pos = approved_pos.filter(procurement__project_id=self.project_filter)

        purchase_vendor_links = PurchaseVendor.objects.select_related(
            "vendor", "po", "po__draft_po"
        ).filter(po__in=approved_pos)

        # Prepare vendor data aggregation
        vendor_data = {}

        for pv in purchase_vendor_links:

            vendor = pv.vendor
            po = pv.po
            dpo = po.draft_po

            vendor_name = vendor.company_name1 or vendor.vendor_name1 or "Unknown Vendor"

            # Convert delivery_weeks → days
            delivery_days = 0
            if dpo and dpo.delivery_weeks:
                ds = dpo.delivery_weeks.strip().lower()
                match = re.match(r"(?i)\s*(\d+)\s*(day|days|week|weeks|month|months|year|years)", ds)
                if match:
                    val, unit = int(match.group(1)), match.group(2)
                    if "day" in unit:
                        delivery_days = val
                    elif "week" in unit:
                        delivery_days = val * 7
                    elif "month" in unit:
                        delivery_days = val * 30
                    elif "year" in unit:
                        delivery_days = val * 365

            committed_price = float(po.po_grandtotal or 0.0)

            vendor_data.setdefault(vendor.id, {
                "vendor_name": vendor_name,
                "procurement_count": 0,
                "total_committed_price": 0.0,
                "total_delivery_days": 0,
                "entries": 0,
                "total_expenditure_price": 0.0,
            })

            vendor_data[vendor.id]["procurement_count"] += 1
            vendor_data[vendor.id]["total_committed_price"] += committed_price
            vendor_data[vendor.id]["total_delivery_days"] += delivery_days
            vendor_data[vendor.id]["entries"] += 1

        # -----------------------------
        # 🔄 Final Vendor Summary
        # -----------------------------
        vendor_summary = []
        for v in vendor_data.values():
            avg = v["total_delivery_days"] / v["entries"] if v["entries"] else 0
            vendor_summary.append({
                "vendor_name": v["vendor_name"],
                "procurement_count": v["procurement_count"],
                "avg_delivery_days": round(avg, 1),
                "total_committed_price": round(v["total_committed_price"], 2),
                "total_expenditure_price": round(v["total_expenditure_price"], 2),
            })

        # -----------------------------
        # 🔄 Top 5 Vendors
        # -----------------------------
        top_vendors = sorted(vendor_summary, key=lambda x: x["procurement_count"], reverse=True)[:5]
        print("Top Vendors:", top_vendors)

        # Final context update
        all_procurement_ids = list(original_procurements.values_list('procurement_id', flat=True))

        # Final data output
        return {
            'top_vendors': top_vendors,
            'procurements_data': procurement_stages,
            'total_procurements': total_procurements,
            'all_procurement_ids': all_procurement_ids, 
            'stage_summary': stage_summary,
            'delivered_procurements': 0,  # Placeholder; delivery tracking not implemented
            'updates': json.dumps(updates),
            'projects': projects_list,
        }
    

 
def get_indentor_dashboard_data(user):
    # Get procurements assigned to this user (non-draft only)
    procurements = Procurement.objects.filter(user=user, is_draft=False)
    all_project_data = None
    projects_data = None
    
    # Get distinct projects linked to these procurements
    if procurements:
        # user_projects = Project.objects.filter(
        #     project_id__in=procurements.values_list('project_id', flat=True)
        # ).distinct()
        user_projects = Project.objects.filter(
            id__in=procurements.values_list('project_id', flat=True)
        ).distinct()


        # Overall dashboard data
        all_project_data = DashboardDataHelper(user, 'user').get_data()

        # Per-project dashboard data
        # projects_data = {
        #     project.project_id: DashboardDataHelper(user, 'user', project.project_id).get_data()
        #     for project in user_projects
        # }
        projects_data = {
            project.project_id: DashboardDataHelper(user, 'user', project.id).get_data()
            for project in user_projects
        }

    return {
        "all_projects": all_project_data,
        "projects_data": projects_data,
    }

def get_RA_dashboard_data(ra_user):
    # Get procurements assigned to this user (non-draft only)
    procurements = Procurement.objects.filter(ra_user=ra_user, is_draft=False)
    all_project_data = None
    projects_data = None    
    #import pdb; pdb.set_trace();
    if procurements:
        # Get distinct projects linked to these procurements
        user_projects = Project.objects.filter(
            id__in=procurements.values_list('project_id', flat=True)
        ).distinct()

        # Overall dashboard data
        all_project_data = DashboardDataHelper(ra_user, 'ra_user').get_data()

        # Per-project dashboard data
        projects_data = {
            project.project_id: DashboardDataHelper(ra_user, 'ra_user',project.id).get_data()
            for project in user_projects
        }

    return {
        "all_projects": all_project_data,
        "projects_data": projects_data,
    }

""" def get_AA_dashboard_data(aa_user):
    #import pdb; #pdb.set_trace
    # Get all projects where user is marked as 'aa_user'
    valid_procurements = Procurement.objects.filter(
        aa_user=aa_user,
        is_draft=False
    ).select_related('project')

    user_projects = Project.objects.filter(
        project_id__in=valid_procurements.values_list('project_id', flat=True)
    ).distinct()

    # Count total number of projects (no FY filter)
    total_projects = user_projects.count()

    # Aggregate total allocated and remaining budgets across all years
    totals = BudgetAllocation.objects.filter(
        project__in=user_projects
    ).aggregate(
        total_allocated=Sum('allocated_budget'),
        total_remaining=Sum('remaining_budget')
    )

    total_allocated_budget = totals['total_allocated'] or 0
    total_remaining_budget = totals['total_remaining'] or 0
    total_used_budget = total_allocated_budget - total_remaining_budget

    # General dashboard data across all related projects
    all_project_data = DashboardDataHelper(aa_user, 'aa_user').get_data()

    # Per-project dashboard data and budgets (across all years)
    projects_data = {}
    for project in user_projects:
        project_budget = BudgetAllocation.objects.filter(
            project=project
        ).aggregate(
            allocated=Sum('allocated_budget'),
            remaining=Sum('remaining_budget')
        )
        allocated = project_budget['allocated'] or 0
        remaining = project_budget['remaining'] or 0
        used = allocated - remaining

        projects_data[project.project_id] = {
            'dashboard_data': DashboardDataHelper(aa_user, 'aa_user', project.project_id).get_data(),
            'allocated_budget': float(allocated),
            'remaining_budget': float(remaining),
            'used_budget': float(used),
        }

    return {
        "all_projects": all_project_data,
        "projects_data": projects_data,
        "total_projects": total_projects,
        "total_allocated_budget": float(total_allocated_budget),
        "total_remaining_budget": float(total_remaining_budget),
        "total_used_budget": float(total_used_budget),
    }
 """
# working function for calculation toatol spent based on the ampunt in the dpo
def get_AA_dashboard_data(aa_user):
    #import pdb; #pdb.set_trace
    # Only procurements where this user is AA
    valid_procurements = Procurement.objects.filter(
        aa_user=aa_user,
        is_draft=False
    ).select_related("project")
    
    projects_data= None;
    total_projects = None;
    total_spent_budget = 0;
    total_allocated_budget = 0;
    total_remaining_budget = 0;

    if valid_procurements:
        user_projects = Project.objects.filter(
            id__in=valid_procurements.values_list("project_id", flat=True)
        ).distinct()

        total_projects = user_projects.count()

        #print(f"\n🔎 DEBUG AA Dashboard for {aa_user}:")
        #print(f"➡️ Total Projects for this AA: {total_projects}")
        #print(f"➡️ Total Procurements for this AA: {valid_procurements.count()}")

        # Allocated budget across all projects
        total_allocated_budget = (
            BudgetAllocation.objects.filter(project__in=user_projects)
            .aggregate(total=Sum("allocated_budget"))["total"] or 0
        )

        # Spent budget = sum of all DPO grand_totals
        # total_spent_budget = (
        #     Purchase_Order.objects.filter(
        #         procurement__project__in=user_projects
        #     ).aggregate(total=Sum("po_grandtotal"))["total"] or 0
        # )
        

        # Only include fully signed POs in spent budget
        # approved_po_ids = (
        #     Purchase_Order.objects
        #     .annotate(
        #         total_approvers=Count('poapproval'),
        #         signed_approvers=Count('poapproval', filter=Q(poapproval__done_sign=True))
        #     )
        #     .filter(total_approvers=F('signed_approvers'))  # ✅ All approvals signed
        #     .values_list('id', flat=True)
        # )

        # total_spent_budget = (
        #     Purchase_Order.objects
        #     .filter(
        #         procurement__project__in=user_projects,
        #         id__in=approved_po_ids  # ✅ Include only fully signed POs
        #     )
        #     .aggregate(total=Sum('po_grandtotal'))['total'] or 0
        # )

        total_spent_budget = (
            Purchase_Order.objects
            .annotate(
                total_approvers=Count('poapproval'),
                signed_approvers=Count('poapproval', filter=Q(poapproval__done_sign=True))
            )
            .filter(
                procurement__project__in=user_projects
            )
            .filter(
                Q(po_sign=True) | Q(total_approvers=F('signed_approvers'))
            )
            .aggregate(total=Sum('po_grandtotal'))['total'] or 0
        )

        total_remaining_budget = total_allocated_budget - total_spent_budget

        #print(f"➡️ TOTAL Allocated Budget: {total_allocated_budget}")
        #print(f"➡️ TOTAL Spent Budget (all POs): {total_spent_budget}")
        #print(f"➡️ TOTAL Remaining Budget: {total_remaining_budget}\n")

        # Per project details
        projects_data = {}
        for project in user_projects:
            allocated = (
                BudgetAllocation.objects.filter(project=project)
                .aggregate(total=Sum("allocated_budget"))["total"] or 0
            )
            # spent = (
            #     Purchase_Order.objects.filter(
            #         procurement__project=project
            #     ).aggregate(total=Sum("po_grandtotal"))["total"] or 0
            # )

            # --- Only include fully signed POs for "spent" ---
            approved_pos = (
                Purchase_Order.objects.filter(procurement__project=project)
                .annotate(
                    total_approvers=Count("poapproval"),
                    signed_approvers=Count("poapproval", filter=Q(poapproval__done_sign=True))
                )
                .filter(
                    Q(po_sign=True) |  # ✅ include directly signed POs
                    Q(total_approvers__gt=0, total_approvers=F("signed_approvers"))  # ✅ fully signed via approvals
                )
            )

            spent = approved_pos.aggregate(total=Sum("po_grandtotal"))["total"] or 0


            remaining = allocated - spent

            project_procurements = valid_procurements.filter(project=project).count()
            project_dpos = DPO.objects.filter(procurement__project=project).count()

            #print(f"📌 Project {project.project_id} - {project.name}")
            #print(f"   • Allocated Budget: {allocated}")
            #print(f"   • Procurements: {project_procurements}")
            #print(f"   • DraftPOs: {project_dpos}")
            #print(f"   • Spent (Sum of DPOs): {spent}")
            #print(f"   • Remaining: {remaining}")

            # Show individual BudgetAllocation rows
            # allocations = BudgetAllocation.objects.filter(project=project)
            # if allocations.exists():
            #     #print("   • Budget Allocations:")
            #     for alloc in allocations:
            #         print(f"      - Allocation {alloc.id}: {alloc.allocated_budget}")
            # else:
            #     print("   • Budget Allocations: None")

            # # Show individual DPO rows
            # pos = Purchase_Order.objects.filter(procurement__project=project)
            # if pos.exists():
            #     print("   • DraftPOs:")
            #     for po in pos:
            #         print(f"      - PO {po.po_number or po.id}: Grand Total {po.po_grandtotal}")
            # else:
            #     print("   • DraftPOs: None")

            # print("\n")

            projects_data[project.project_id] = {
                "dashboard_data": DashboardDataHelper(aa_user, "aa_user", project.id).get_data(),
                "allocated_budget": float(allocated),
                "spent_budget": float(spent),
                "remaining_budget": float(remaining),
            }

    return {
        "all_projects": DashboardDataHelper(aa_user, "aa_user").get_data(),
        "projects_data": projects_data,
        "total_projects": total_projects,
        "total_allocated_budget": float(total_allocated_budget),
        "total_used_budget": float(total_spent_budget),
        "total_remaining_budget": float(total_remaining_budget),
    }

def get_financial_year(current_date):
    """
    Determines the financial year for a given date.
    Params: current_date: The date for which the financial year is calculated.
    Returns: The financial year in 'YYYY-YYYY' format.
    """
   
    # Extract the year part from the input date
    year = current_date.year
 
    # If the date is in or after April (month 4), the financial year starts this year and ends next year
    if current_date.month >= 4:  # April to December
        return f"{year}-{year + 1}"
    else:
        # If the date is from January to March, the financial year started the previous year
        return f"{year - 1}-{year}"
 
def get_month_range_for_financial_year(financial_year):
    """
    Given a financial year in the format 'YYYY-YYYY', return the start and end dates
    of that financial year.
    Params: financial_year (str): The financial year in the format 'YYYY-YYYY'.
    Returns:(start_date, end_date)
    """
 
    # Validate that input is a string and is in the correct 'YYYY-YYYY' format
    if not isinstance(financial_year, str) or len(financial_year.split('-')) != 2:
        raise ValueError(f"Invalid financial year format: {financial_year}. Expected format: 'YYYY-YYYY'.")
 
    try:
        # Split the string and convert both parts to integers
        start_year, end_year = map(int, financial_year.split('-'))
    except ValueError as e:
        # Raise a more meaningful error if conversion fails
        raise ValueError(f"Invalid financial year format: {financial_year}. Expected format: 'YYYY-YYYY'.")
 
    # Define the start of the financial year: April 1st of the first year
    start_date = date(start_year, 4, 1)
 
    # Define the end of the financial year: March 31st of the next year
    end_date = date(end_year, 3, 31)
 
    # Return the start and end dates as a tuple
    return start_date, end_date

def get_accounts_dashboard_data(user, financial_year=None, quarter=None, source_filter="all"):
    
        if financial_year:
            financial_years_list = [fy.strip() for fy in financial_year.split(',')]
        else:
            # Default: current FY only
            financial_years_list = [get_financial_year(date.today())]

        # Compute combined date range spanning all requested FYs
        all_start_dates = []
        all_end_dates = []

        for fy in financial_years_list:
            try:
                start_date, end_date = get_month_range_for_financial_year(fy)
                all_start_dates.append(start_date)
                all_end_dates.append(end_date)
            except ValueError:
                # Skip invalid FY formats gracefully
                continue

        if not all_start_dates or not all_end_dates:
            # Fallback if no valid FYs found
            today = date.today()
            financial_year = get_financial_year(today)
            start_date, end_date = get_month_range_for_financial_year(financial_year)
            financial_years_list = [financial_year]
        else:
            start_date = min(all_start_dates)
            end_date = max(all_end_dates)

        # Filter projects that have allocations in ANY of the requested FYs
        # or procurements with expected dates in the combined date range
        projects = Project.objects.filter(
            Q(budgetallocation__financial_year__in=financial_years_list) |
            Q(procurement__particular__datequantity__expected_date__range=(start_date, end_date))
        ).distinct()

        # Total projects count for all FYs combined
        total_projects = Project.objects.filter(
            budgetallocation__financial_year__in=financial_years_list
        ).distinct().count()

        # Aggregate total allocated and remaining budgets across all FYs combined
        totals = BudgetAllocation.objects.filter(financial_year__in=financial_years_list).aggregate(
            total_allocated=Sum('allocated_budget'),
            total_remaining=Sum('remaining_budget')
        )

        total_allocated_budget = totals['total_allocated'] or Decimal(0)
        total_remaining_budget = totals['total_remaining'] or Decimal(0)
        
        total_used_budget = total_allocated_budget - total_remaining_budget
        financial_years = BudgetAllocation.objects.values_list('financial_year', flat=True).distinct()

        ordered_months = list(month_name[4:]) + list(month_name[1:4])  # Apr to Mar

        # Initialize your defaultdicts and dicts here
        monthly_planned_totals_import = defaultdict(lambda: {month: Decimal(0) for month in ordered_months})
        monthly_committed_totals_import = defaultdict(lambda: {month: Decimal(0) for month in ordered_months})
        monthly_planned_totals_indigenous = defaultdict(lambda: {month: Decimal(0) for month in ordered_months})
        monthly_committed_totals_indigenous = defaultdict(lambda: {month: Decimal(0) for month in ordered_months})
        monthly_planned_totals_combined = defaultdict(lambda: {month: Decimal(0) for month in ordered_months})
        monthly_committed_totals_combined = defaultdict(lambda: {month: Decimal(0) for month in ordered_months})

        overall_planned_totals_import = {month: Decimal(0) for month in ordered_months}
        overall_committed_totals_import = {month: Decimal(0) for month in ordered_months}
        overall_planned_totals_indigenous = {month: Decimal(0) for month in ordered_months}
        overall_committed_totals_indigenous = {month: Decimal(0) for month in ordered_months}
        overall_planned_totals_combined = {month: Decimal(0) for month in ordered_months}
        overall_committed_totals_combined = {month: Decimal(0) for month in ordered_months}

        contributing_procurements = defaultdict(lambda: {'planned': defaultdict(dict), 'committed': defaultdict(list)})
        previous_values = {}
        rows = []
        for project in projects:
            row = {
                'project_id': project.project_id,
                'project_name': project.name,
                'monthly_planned_values_combined': [],
                'monthly_committed_values_combined': [],
                'monthly_planned_values_import': [],
                'monthly_committed_values_import': [],
                'monthly_planned_values_indigenous': [],
                'monthly_committed_values_indigenous': [],
            }

            # Sum allocated budget across ALL selected FYs for this project
            allocated_budget_objs = BudgetAllocation.objects.filter(project=project, financial_year__in=financial_years_list)
            allocated_budget = sum([obj.allocated_budget for obj in allocated_budget_objs]) if allocated_budget_objs else Decimal(0)
            
            for procurement in Procurement.objects.filter(project=project, cancellation=False, is_draft=False):

                # Determine source type and creator
                source_type = procurement.import_indigenous.source_type if procurement.import_indigenous else None
                creator_user = procurement.user or procurement.imm_user or procurement.ra_user or procurement.aa_user or procurement.account_user or procurement.ri_user
                creator_name = f"{creator_user.first_name} {creator_user.last_name}".strip() if creator_user else "Unknown"

                # Resolve original procurement ID
                if procurement.modificationpr:
                    original_id = procurement.modifiedpr_id.replace('M', '').split('-')[0]
                    original_procurement = Procurement.objects.filter(procurement_id=original_id, is_draft=False).first()
                    if original_procurement:
                        creator_user = (
                            original_procurement.user or original_procurement.imm_user or
                            original_procurement.ra_user or original_procurement.aa_user or
                            original_procurement.account_user or original_procurement.ri_user
                        )
                        creator_name = f"{creator_user.first_name} {creator_user.last_name}".strip() if creator_user else "Unknown"
                    original_id = original_procurement.procurement_id if original_procurement else original_id
                else:
                    original_id = procurement.procurement_id

                # Collect all due dates (irrespective of FY filter)
                all_due_dates = [
                    d for particular in procurement.particular.all()
                    for d in particular.datequantity.all().values_list('expected_date', flat=True)
                    if d is not None
                ]

                if not all_due_dates:
                    continue  # No due dates, skip

                # Compute latest due date and its FY
                latest_due_date = max(all_due_dates)
                procurement_fy = get_financial_year(latest_due_date)

                if procurement_fy not in financial_years_list:
                    continue  # FY filter applied, skip

                # Check budget for this FY
                has_budget = BudgetAllocation.objects.filter(project=project, financial_year=procurement_fy).exists()
                if not has_budget:
                    continue

                # Determine month label and estimated value
                due_month = latest_due_date.month
                month_label = month_name[due_month]
                estimated_value = sum([
                    particular.estimatedvalue or Decimal(0) for particular in procurement.particular.all()
                ])

                # Remove procurement from ALL months in ALL financial years it might have appeared
                prev_data = previous_values.get(original_id)
                if prev_data:
                    prev_value = prev_data['value']

                    # Remove from all months in planned totals and contributing_procurements
                    for m in contributing_procurements[project.project_id]['planned']:
                        if original_id in contributing_procurements[project.project_id]['planned'][m]:
                            # Subtract old value from totals
                            if source_type == 'Import':
                                monthly_planned_totals_import[project][m] -= prev_value
                            elif source_type == 'Indigenous':
                                monthly_planned_totals_indigenous[project][m] -= prev_value

                            # Remove from contributing list
                            contributing_procurements[project.project_id]['planned'][m].pop(original_id, None)

                # Add procurement in the month/FY of latest due date
                if source_type == 'Import':
                    monthly_planned_totals_import[project][month_label] += estimated_value
                elif source_type == 'Indigenous':
                    monthly_planned_totals_indigenous[project][month_label] += estimated_value

                # Save current state
                previous_values[original_id] = {'value': estimated_value, 'month': month_label}

                contributing_procurements[project.project_id]['planned'][month_label][original_id] = {
                    'procurement_id': original_id,
                    'estimated_value': float(estimated_value),
                    'creator': creator_name,
                    'source_of_make': source_type
                }
                import pdb;#######pdb.set_trace()
                # Handle committed values (POs)
                for dpo in procurement.draft_pos.all():
                    po = dpo.final_po.first()
                    if not po:
                        continue
                    purchase_orders = Purchase_Order.objects.filter(draft_po=dpo)

                    for po in purchase_orders:
                        # If no PO_grandtotal, skip
                        if not po.po_grandtotal:
                            #print(f"[DEBUG] Skipping PO {po.po_number} because po_grandtotal is missing or zero")
                            continue

                        #print(f"[DEBUG] Processing PO: {po.po_number}, draft_po ID: {dpo.id}, "
                               # f"Procurement: {procurement.procurement_id}, PO GrandTotal: {po.po_grandtotal}, "
                               # f"DPO delivery_weeks: {dpo.delivery_weeks}")


                        # dpo.delivery_weeks = "7 weeks" or "8days" or "1 year"
                        delivery_str = dpo.delivery_weeks or ''
                        delivery_str = delivery_str.strip().lower()

                        # Regex to capture number and unit (e.g., "7 weeks")
                        match = re.match(r'(\d+)\s*(day|days|week|weeks|month|months|year|years)?', delivery_str)

                        if match:
                            value = int(match.group(1))
                            unit = match.group(2) or 'weeks'  # Default to weeks if unit is missing
                            unit = unit.rstrip('s')  # Normalize to singular form

                            if unit == 'day':
                                delta = timedelta(days=value)
                            elif unit == 'week':
                                delta = timedelta(weeks=value)
                            elif unit == 'month':
                                delta = relativedelta(months=value)
                            elif unit == 'year':
                                delta = relativedelta(years=value)
                            else:
                                delta = timedelta(weeks=value)  # Fallback

                            expected_delivery_date = (po.date_created + delta).date()
                        else:
                            expected_delivery_date = po.date_created.date()  # Default if parsing fails

                        committed_fy = get_financial_year(expected_delivery_date)
                        #print(f"[DEBUG] Expected delivery date: {expected_delivery_date}, Committed FY: {committed_fy}")

                        if committed_fy not in financial_years_list:
                            #print(f"[DEBUG] Skipping PO {po.po_number} because FY {committed_fy} not in {financial_years_list}")
                            continue

                        if not (start_date <= expected_delivery_date <= end_date):
                            #print(f"[DEBUG] Skipping PO {po.po_number} because date {expected_delivery_date} not in range {start_date} to {end_date}")
                            continue
                        # calculate the committed month for that procurement based on PO generated date and delivery weeks
                        committed_month = expected_delivery_date.month
                        committed_month_label = month_name[committed_month]

                        # Add committed value from PO_grandtotal
                        committed_value = po.po_grandtotal

                        #print(f"[DEBUG] Committed value: {committed_value} added for month {committed_month_label}")

                        if source_type == 'Import':
                            monthly_committed_totals_import[project][committed_month_label] += committed_value
                        elif source_type == 'Indigenous':
                            monthly_committed_totals_indigenous[project][committed_month_label] += committed_value

                        contributing_procurements[project.project_id]['committed'][committed_month_label].append({
                            'procurement_id': procurement.procurement_id,
                            'committed_value': float(committed_value),
                            'creator': creator_name,
                            'source_of_make': source_type
                        })

            # Combine monthly totals per project
            for month in ordered_months:
                monthly_planned_totals_combined[project][month] = (
                    monthly_planned_totals_import[project][month] +
                    monthly_planned_totals_indigenous[project][month]
                )
                monthly_committed_totals_combined[project][month] = (
                    monthly_committed_totals_import[project][month] +
                    monthly_committed_totals_indigenous[project][month]
                )

                overall_planned_totals_import[month] += monthly_planned_totals_import[project][month]
                overall_committed_totals_import[month] += monthly_committed_totals_import[project][month]
                overall_planned_totals_indigenous[month] += monthly_planned_totals_indigenous[project][month]
                overall_committed_totals_indigenous[month] += monthly_committed_totals_indigenous[project][month]
                overall_planned_totals_combined[month] += monthly_planned_totals_combined[project][month]
                overall_committed_totals_combined[month] += monthly_committed_totals_combined[project][month]

            row['allocated_budget'] = float(allocated_budget)
            row['monthly_planned_values_combined'] = [float(monthly_planned_totals_combined[project][month]) for month in ordered_months]
            row['monthly_committed_values_combined'] = [float(monthly_committed_totals_combined[project][month]) for month in ordered_months]
            row['monthly_planned_values_import'] = [float(monthly_planned_totals_import[project][month]) for month in ordered_months]
            row['monthly_planned_values_indigenous'] = [float(monthly_planned_totals_indigenous[project][month]) for month in ordered_months]
            row['monthly_committed_values_import'] = [float(monthly_committed_totals_import[project][month]) for month in ordered_months]
            row['monthly_committed_values_indigenous'] = [float(monthly_committed_totals_indigenous[project][month]) for month in ordered_months]

            rows.append(row)

        # Convert contributing planned dicts to lists for JSON serialization
        for project_id, contrib in contributing_procurements.items():
            for month_label in contrib['planned']:
                contrib['planned'][month_label] = list(contrib['planned'][month_label].values())
        context = {
            'rows': rows,
            'months': ordered_months,
            'financial_years': list(financial_years),
            'total_allocated_budget': float(total_allocated_budget),
            'overall_planned_totals_import': {month: float(overall_planned_totals_import[month]) for month in ordered_months},
            'overall_committed_totals_import': {month: float(overall_committed_totals_import[month]) for month in ordered_months},
            'overall_planned_totals_indigenous': {month: float(overall_planned_totals_indigenous[month]) for month in ordered_months},
            'overall_committed_totals_indigenous': {month: float(overall_committed_totals_indigenous[month]) for month in ordered_months},
            'overall_planned_totals_combined': {month: float(overall_planned_totals_combined[month]) for month in ordered_months},
            'overall_committed_totals_combined': {month: float(overall_committed_totals_combined[month]) for month in ordered_months},
            'contributing_procurements': contributing_procurements,
            'total_projects': total_projects,
            'total_remaining_budget': total_remaining_budget,
            'total_used_budget':total_used_budget
        }

        return context

def get_aa_budget_data(user, financial_year=None, quarter=None, source_filter="all"):
    
        if financial_year:
            financial_years_list = [fy.strip() for fy in financial_year.split(',')]
        else:
            # Default: current FY only
            financial_years_list = [get_financial_year(date.today())]

        # Compute combined date range spanning all requested FYs
        all_start_dates = []
        all_end_dates = []

        for fy in financial_years_list:
            try:
                start_date, end_date = get_month_range_for_financial_year(fy)
                all_start_dates.append(start_date)
                all_end_dates.append(end_date)
            except ValueError:
                # Skip invalid FY formats gracefully
                continue

        if not all_start_dates or not all_end_dates:
            # Fallback if no valid FYs found
            today = date.today()
            financial_year = get_financial_year(today)
            start_date, end_date = get_month_range_for_financial_year(financial_year)
            financial_years_list = [financial_year]
        else:
            start_date = min(all_start_dates)
            end_date = max(all_end_dates)

        # Filter projects that have allocations in ANY of the requested FYs
        # or procurements with expected dates in the combined date range
        projects = Project.objects.filter(
            Q(budgetallocation__financial_year__in=financial_years_list) |
            Q(procurement__particular__datequantity__expected_date__range=(start_date, end_date))
        ).distinct()

         # Aggregate total allocated and remaining budgets across all FYs combined
        totals = BudgetAllocation.objects.filter(financial_year__in=financial_years_list).aggregate(
            total_allocated=Sum('allocated_budget'),
        )

        total_allocated_budget = totals['total_allocated'] or Decimal(0)

        financial_years = BudgetAllocation.objects.values_list('financial_year', flat=True).distinct()

        ordered_months = list(month_name[4:]) + list(month_name[1:4])  # Apr to Mar

        # Initialize your defaultdicts and dicts here
        monthly_planned_totals_import = defaultdict(lambda: {month: Decimal(0) for month in ordered_months})
        monthly_committed_totals_import = defaultdict(lambda: {month: Decimal(0) for month in ordered_months})
        monthly_planned_totals_indigenous = defaultdict(lambda: {month: Decimal(0) for month in ordered_months})
        monthly_committed_totals_indigenous = defaultdict(lambda: {month: Decimal(0) for month in ordered_months})
        monthly_planned_totals_combined = defaultdict(lambda: {month: Decimal(0) for month in ordered_months})
        monthly_committed_totals_combined = defaultdict(lambda: {month: Decimal(0) for month in ordered_months})

        overall_planned_totals_import = {month: Decimal(0) for month in ordered_months}
        overall_committed_totals_import = {month: Decimal(0) for month in ordered_months}
        overall_planned_totals_indigenous = {month: Decimal(0) for month in ordered_months}
        overall_committed_totals_indigenous = {month: Decimal(0) for month in ordered_months}
        overall_planned_totals_combined = {month: Decimal(0) for month in ordered_months}
        overall_committed_totals_combined = {month: Decimal(0) for month in ordered_months}

        contributing_procurements = defaultdict(lambda: {'planned': defaultdict(dict), 'committed': defaultdict(list)})
        previous_values = {}
        rows = []
        for project in projects:
            row = {
                'project_id': project.project_id,
                'project_name': project.name,
                'monthly_planned_values_combined': [],
                'monthly_committed_values_combined': [],
                'monthly_planned_values_import': [],
                'monthly_committed_values_import': [],
                'monthly_planned_values_indigenous': [],
                'monthly_committed_values_indigenous': [],
            }

            # Sum allocated budget across ALL selected FYs for this project
            allocated_budget_objs = BudgetAllocation.objects.filter(project=project, financial_year__in=financial_years_list)
            allocated_budget = sum([obj.allocated_budget for obj in allocated_budget_objs]) if allocated_budget_objs else Decimal(0)
            
            for procurement in Procurement.objects.filter(project=project, cancellation=False, is_draft=False):

                # Determine source type and creator
                source_type = procurement.import_indigenous.source_type if procurement.import_indigenous else None
                creator_user = procurement.user or procurement.imm_user or procurement.ra_user or procurement.aa_user or procurement.account_user or procurement.ri_user
                creator_name = f"{creator_user.first_name} {creator_user.last_name}".strip() if creator_user else "Unknown"


                # Resolve original procurement ID
                if procurement.modificationpr:
                    original_id = procurement.modifiedpr_id.replace('M', '').split('-')[0]
                    original_procurement = Procurement.objects.filter(procurement_id=original_id, is_draft=False).first()
                    if original_procurement:
                        creator_user = (
                            original_procurement.user or original_procurement.imm_user or
                            original_procurement.ra_user or original_procurement.aa_user or
                            original_procurement.account_user or original_procurement.ri_user
                        )
                        creator_name = f"{creator_user.first_name} {creator_user.last_name}".strip() if creator_user else "Unknown"
                    original_id = original_procurement.procurement_id if original_procurement else original_id
                else:
                    original_id = procurement.procurement_id

                # Collect all due dates (irrespective of FY filter)
                all_due_dates = [
                    d for particular in procurement.particular.all()
                    for d in particular.datequantity.all().values_list('expected_date', flat=True)
                    if d is not None
                ]

                if not all_due_dates:
                    continue  # No due dates, skip

                # Compute latest due date and its FY
                latest_due_date = max(all_due_dates)
                procurement_fy = get_financial_year(latest_due_date)

                if procurement_fy not in financial_years_list:
                    continue  # FY filter applied, skip

                # Check budget for this FY
                has_budget = BudgetAllocation.objects.filter(project=project, financial_year=procurement_fy).exists()
                if not has_budget:
                    continue

                # Determine month label and estimated value
                due_month = latest_due_date.month
                month_label = month_name[due_month]
                estimated_value = sum([
                    particular.estimatedvalue or Decimal(0) for particular in procurement.particular.all()
                ])

                # Remove procurement from ALL months in ALL financial years it might have appeared
                prev_data = previous_values.get(original_id)
                if prev_data:
                    prev_value = prev_data['value']

                    # Remove from all months in planned totals and contributing_procurements
                    for m in contributing_procurements[project.project_id]['planned']:
                        if original_id in contributing_procurements[project.project_id]['planned'][m]:
                            # Subtract old value from totals
                            if source_type == 'Import':
                                monthly_planned_totals_import[project][m] -= prev_value
                            elif source_type == 'Indigenous':
                                monthly_planned_totals_indigenous[project][m] -= prev_value

                            # Remove from contributing list
                            contributing_procurements[project.project_id]['planned'][m].pop(original_id, None)

                # Add procurement in the month/FY of latest due date
                if source_type == 'Import':
                    monthly_planned_totals_import[project][month_label] += estimated_value
                elif source_type == 'Indigenous':
                    monthly_planned_totals_indigenous[project][month_label] += estimated_value

                # Save current state
                previous_values[original_id] = {'value': estimated_value, 'month': month_label}

                contributing_procurements[project.project_id]['planned'][month_label][original_id] = {
                    'procurement_id': original_id,
                    'estimated_value': float(estimated_value),
                    'creator': creator_name,
                    'source_of_make': source_type
                }

                # Handle committed values (POs)
                all_pos = Purchase_Order.objects.filter(procurement=procurement).prefetch_related("poapproval_set")
                
                for dpo in procurement.draft_pos.all():
                    po = dpo.final_po.first()
                    if not po:
                        continue

                    # dpo.delivery_weeks = "7 weeks" or "8days" or "1 year"
                    delivery_str = dpo.delivery_weeks or ''
                    delivery_str = delivery_str.strip().lower()

                    # Regex to capture number and unit (e.g., "7 weeks")
                    match = re.match(r'(\d+)\s*(day|days|week|weeks|month|months|year|years)?', delivery_str)

                    if match:
                        value = int(match.group(1))
                        unit = match.group(2) or 'weeks'  # Default to weeks if unit is missing
                        unit = unit.rstrip('s')  # Normalize to singular form

                        if unit == 'day':
                            delta = timedelta(days=value)
                        elif unit == 'week':
                            delta = timedelta(weeks=value)
                        elif unit == 'month':
                            delta = relativedelta(months=value)
                        elif unit == 'year':
                            delta = relativedelta(years=value)
                        else:
                            delta = timedelta(weeks=value)  # Fallback

                        expected_delivery_date = (po.date_created + delta).date()
                    else:
                        expected_delivery_date = po.date_created.date()  # Default if parsing fails

                    committed_fy = get_financial_year(expected_delivery_date)
                    if committed_fy not in financial_years_list:
                        continue

                    if not (start_date <= expected_delivery_date <= end_date):
                        continue
                    # calculate the committed month for that procurement based on PO generated date and delivery weeks
                    committed_month = expected_delivery_date.month
                    committed_month_label = month_name[committed_month]

                    if source_type == 'Import':
                        monthly_committed_totals_import[project][committed_month_label] += dpo.grand_total
                    elif source_type == 'Indigenous':
                        monthly_committed_totals_indigenous[project][committed_month_label] += dpo.grand_total

                    contributing_procurements[project.project_id]['committed'][committed_month_label].append({
                        'procurement_id': procurement.procurement_id,
                        'committed_value': float(dpo.grand_total),
                        'creator': creator_name,
                        'source_of_make': source_type
                    })

            # Combine monthly totals per project
            for month in ordered_months:
                monthly_planned_totals_combined[project][month] = (
                    monthly_planned_totals_import[project][month] +
                    monthly_planned_totals_indigenous[project][month]
                )
                monthly_committed_totals_combined[project][month] = (
                    monthly_committed_totals_import[project][month] +
                    monthly_committed_totals_indigenous[project][month]
                )

                overall_planned_totals_import[month] += monthly_planned_totals_import[project][month]
                overall_committed_totals_import[month] += monthly_committed_totals_import[project][month]
                overall_planned_totals_indigenous[month] += monthly_planned_totals_indigenous[project][month]
                overall_committed_totals_indigenous[month] += monthly_committed_totals_indigenous[project][month]
                overall_planned_totals_combined[month] += monthly_planned_totals_combined[project][month]
                overall_committed_totals_combined[month] += monthly_committed_totals_combined[project][month]

            row['allocated_budget'] = float(allocated_budget)
            row['monthly_planned_values_combined'] = [float(monthly_planned_totals_combined[project][month]) for month in ordered_months]
            row['monthly_committed_values_combined'] = [float(monthly_committed_totals_combined[project][month]) for month in ordered_months]
            row['monthly_planned_values_import'] = [float(monthly_planned_totals_import[project][month]) for month in ordered_months]
            row['monthly_planned_values_indigenous'] = [float(monthly_planned_totals_indigenous[project][month]) for month in ordered_months]
            row['monthly_committed_values_import'] = [float(monthly_committed_totals_import[project][month]) for month in ordered_months]
            row['monthly_committed_values_indigenous'] = [float(monthly_committed_totals_indigenous[project][month]) for month in ordered_months]

            rows.append(row)

        # Convert contributing planned dicts to lists for JSON serialization
        for project_id, contrib in contributing_procurements.items():
            for month_label in contrib['planned']:
                contrib['planned'][month_label] = list(contrib['planned'][month_label].values())
        context = {
            'rows': rows,
            'months': ordered_months,
            'financial_years': list(financial_years),
            'total_allocated_budget': float(total_allocated_budget),
            'overall_planned_totals_import': {month: float(overall_planned_totals_import[month]) for month in ordered_months},
            'overall_committed_totals_import': {month: float(overall_committed_totals_import[month]) for month in ordered_months},
            'overall_planned_totals_indigenous': {month: float(overall_planned_totals_indigenous[month]) for month in ordered_months},
            'overall_committed_totals_indigenous': {month: float(overall_committed_totals_indigenous[month]) for month in ordered_months},
            'overall_planned_totals_combined': {month: float(overall_planned_totals_combined[month]) for month in ordered_months},
            'overall_committed_totals_combined': {month: float(overall_committed_totals_combined[month]) for month in ordered_months},
            'contributing_procurements': contributing_procurements,
        }

        return context
