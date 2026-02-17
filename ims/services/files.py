import pdb
from django.db.models import Q, Max
import pandas as pd
from requests import request
from ims.models import *
from datetime import datetime
from dateutil.relativedelta import relativedelta


def get_ra_procurement_data(request, user):
    # Fetch department info
    try:
        user_reg = UserReg.objects.get(user=user)
        department = user_reg.user_dept
    except UserReg.DoesNotExist:
        department = None

    # Filter users based on department presence
    if department:
        users = UserReg.objects.filter(
            Q(role__role="IMM") | Q(role__role="Indentor IMM")
        ).values(
            "emp_id", "user__id", "user__first_name", "user__last_name", "user_dept__dept_name"
        )
    else:
        users = UserReg.objects.filter(
            Q(role__role="IMM") | Q(role__role="Indentor IMM")
        ).values(
            "emp_id", "user__id", "user__first_name", "user__last_name", "user_dept__dept_name"
        )

    user_list = [
        {
            "emp_id": u["emp_id"],
            "first_name": u["user__first_name"],
            "last_name": u["user__last_name"],
            "full_name": f"{u['user__first_name']} {u['user__last_name']}"
        }
        for u in users
    ]

    try:
        rapr = pd.DataFrame(
            StageProgress.objects.filter(
                stagename__stage="stage1",
                remarktype__in=["PR_Raised", "Approval", "Modified"]
            ).values("procurement_id__procurement_id")
        ).drop_duplicates(subset=["procurement_id__procurement_id"])["procurement_id__procurement_id"].to_list()

        start_date_str = request.GET.get("startDate")
        end_date_str = request.GET.get("endDate")
        status_filter = request.GET.get("statusFilter")
        # ##pdb.set_trace()
        if "ra_prids" in request.session and request.session["ra_prids"]:
            raw_prids = request.session["ra_prids"]
            print("raw_prids:", raw_prids)

            # ✅ REMOVE ONLY THIS SESSION KEY AFTER USING IT
            request.session.pop("ra_prids", None)
            print("Removed ra_prids from session")
        else:
            print("ra_prids NOT found or empty")
            raw_prids = None


        ##print("start_date_str:", start_date_str)
        #print("end_date_str:", end_date_str)
        #print("status_filter:", status_filter)
        print("ra ------------------------------------>")
        procurements_qs = Procurement.objects.filter(
            procurement_id__in=rapr,
            ra_user=user,
            is_draft=False,
            modificationpr=False
        ).annotate(
            latest_stage1_datetime=Max(
                'prid__datetime',
                filter=Q(prid__stagename__stage='stage1', prid__remarktype__in=["PR_Raised", "Approval", "Modified"])
            )
        ).order_by('-latest_stage1_datetime', '-id')

        procurements = procurements_qs  # Now we assign procurements_qs to procurements
        
        #print('procurements_qs', procurements_qs)

        try:
            today = datetime.today().date()

            if start_date_str:
                try:
                    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                except ValueError:
                    start_date = None
            else:
                start_date = None

            if end_date_str:
                try:
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                except ValueError:
                    end_date = None
            else:
                end_date = None

            pr_only_list = []
            pr_vendor_pairs = []
            # ##pdb.set_trace()
    
            # if raw_prids:
            #     pr_only_list = []
            #     pr_vendor_pairs = []
            #     pr_part_pairs = []  # NEW: PR–Particular pairs

            #     items = [x.strip() for x in raw_prids.split(",") if x.strip()]

            #     # Categorize each item
            #     for element in items:

            #         # CASE A: Negotiation PR_Particular pair (e.g., PR100_P12)
            #         if "_P" in element:
            #             pr_id, part_id = element.split("_P")
            #             pr_part_pairs.append({
            #                 "pr_id": pr_id.strip(),
            #                 "particular_id": int(part_id.strip())
            #             })
            #             continue

            #         # CASE B: Vendor pair (e.g., PR100-5)
            #         if "-" in element:
            #             pr_id, vendor_id = element.split("-")
            #             pr_vendor_pairs.append({
            #                 "pr_id": pr_id.strip(),
            #                 "vendor_id": int(vendor_id.strip())
            #             })
            #             continue

            #         # CASE C: PR only
            #         pr_only_list.append(element.strip())

            #     # ==========================================================
            #     # CASE 1 — ONLY PR IDs (no vendor, no particular)
            #     # ==========================================================
            #     if pr_only_list and not pr_vendor_pairs and not pr_part_pairs:
            #         procurements = procurements.filter(procurement_id__in=pr_only_list)

            #     # ==========================================================
            #     # CASE 2 — PR + PARTICULAR pairs (Negotiation-based)
            #     # ==========================================================
            #     elif pr_part_pairs:
            #         filtered_negos = []

            #         for pair in pr_part_pairs:
            #             pr = pair["pr_id"]
            #             part = pair["particular_id"]

            #             nego = Negotiation.objects.filter(
            #                 quoted_vendors__csparticular__procurement__procurement_id=pr,
            #                 quoted_vendors__csparticular_id=part
            #             ).first()

            #             if nego:
            #                 filtered_negos.append(nego)

            #         if filtered_negos:
            #             valid_pr_ids = {
            #                 nego.quoted_vendors.csparticular.procurement.procurement_id
            #                 for nego in filtered_negos
            #             }
            #             procurements = procurements.filter(procurement_id__in=valid_pr_ids)
            #             request.vendor_filtered_negotiations = filtered_negos
            #         else:
            #             procurements = procurements.none()

            #     # ==========================================================
            #     # CASE 3 — PR + VENDOR pairs (DPO or PO)
            #     # ==========================================================
            #     elif pr_vendor_pairs:
            #         filtered_dpos = []
            #         filtered_pos = []

            #         for pair in pr_vendor_pairs:
            #             pr = pair["pr_id"]
            #             vendor = pair["vendor_id"]

            #             dpo = DPO.objects.filter(
            #                 procurement__procurement_id=pr,
            #                 sources__id=vendor
            #             ).first()

            #             po = Purchase_Order.objects.filter(
            #                 procurement__procurement_id=pr,
            #                 draft_po__sources__id=vendor
            #             ).first()

            #             if dpo:
            #                 filtered_dpos.append(dpo)
            #             if po:
            #                 filtered_pos.append(po)

            #         if filtered_dpos:
            #             valid_pr_ids = {dpo.procurement.procurement_id for dpo in filtered_dpos}
            #             procurements = procurements.filter(procurement_id__in=valid_pr_ids)
            #             request.vendor_filtered_dpos = filtered_dpos

            #         elif filtered_pos:
            #             valid_pr_ids = {po.procurement.procurement_id for po in filtered_pos}
            #             procurements = procurements.filter(procurement_id__in=valid_pr_ids)
            #             request.vendor_filtered_pos = filtered_pos

            #         else:
            #             procurements = procurements.none()

            #     # ==========================================================
            #     # CASE 4 — NONE matched / empty
            #     # ==========================================================
            #     else:
            #         procurements = procurements.none()

            if raw_prids:
                procurements = procurements.filter(procurement_id__in=[pr.strip() for pr in raw_prids.split(",") if pr.strip()])
            elif start_date and end_date:
                procurements = procurements.filter(datetime__date__gte=start_date, datetime__date__lte=end_date)
            elif start_date and not end_date:
                procurements = procurements.filter(datetime__date__gte=start_date, datetime__date__lte=today)
            elif not start_date and end_date:
                procurements = procurements.filter(datetime__date__lte=end_date)
            elif not start_date and not end_date:
                # Default: current + previous month
                first_day_current_month = today.replace(day=1)
                first_day_previous_month = first_day_current_month - relativedelta(months=1)
                procurements = procurements.filter(datetime__date__gte=first_day_previous_month)
        except Exception as e:
            print("Date filtering error:", e)

        status_list = []
        for procurement in procurements:
            remarks = set()

            # ✅ Reject
            reject_remarks = StageProgress.objects.filter(
                procurement_id__procurement_id=procurement.procurement_id,
                remarktype="Reject"
            ).values_list("remarktype", flat=True).distinct()
            remarks.update(reject_remarks)

            # ✅ Modified
            modified_remarks = StageProgress.objects.filter(
                procurement_id__procurement_id=procurement.procurement_id,
                remarktype="Modified"
            ).values_list("remarktype", flat=True).distinct()
            remarks.update(modified_remarks)

            # ✅ Stage 5 Approval (latest only)
            latest_stage5 = (
                StageProgress.objects.filter(
                    procurement_id__procurement_id=procurement.procurement_id,
                    stagename__stage="stage5"
                )
                .order_by("-datetime")
                .values_list("remarktype", flat=True)
                .first()
            )
            if latest_stage5 == "Approval":
                remarks.add("Approval")


            status_list.append({
                "procurement_id": procurement.procurement_id,
                "statuses": list(remarks)
            })

            last_remark = StageProgress.objects.filter(
                procurement_id__procurement_id=procurement.procurement_id
            ).values("stagename__stage", "remarktype").last()

            if last_remark and last_remark["stagename__stage"] == "stage1" and last_remark["remarktype"] in ["PR_Raised", "Approval", "Modified"]:
                procurement.action_performed = True
            else:
                procurement.action_performed = False

            # procurement.save()

    except Exception as e:
        #print(f"Error: {e}")
        procurements = []
        status_list = []

    # FINAL ORDERING (cross-platform stable)
    # ⭐ FINAL ORDERING — fix PR ordering issue
    procurements = sorted(
        procurements,
        key=lambda p: (
            p.latest_stage1_datetime or p.datetime or datetime.min
        ),
        reverse=True
    )



    return {
        "users": user_list,
        "procurements": procurements,
        "status_list": status_list,
    }


def get_reject_ra_procurement_data(request, user):
 

    try:
        
        # Get procurement IDs rejected by user at stage2
        rejimmpr = pd.DataFrame(
            StageProgress.objects.filter(
                rejectstage__stage="stage2",
                remarktype="Reject",
                rejectuser=user
            ).values("procurement_id__procurement_id")
        ).drop_duplicates(subset=["procurement_id__procurement_id"])["procurement_id__procurement_id"].to_list()

        start_date_str = request.GET.get("startDate")
        end_date_str = request.GET.get("endDate")
        status_filter = request.GET.get("statusFilter")

        #print("start_date_str:", start_date_str)
        #print("end_date_str:", end_date_str)
        #print("status_filter:", status_filter)
        # ####pdb.set_trace()
        # Get procurements with latest reject datetime annotated
        procurements_qs = Procurement.objects.filter(
            procurement_id__in=rejimmpr,
            is_draft=False
        ).annotate(
            latest_reject_datetime=Max(
                'prid__datetime',
                filter=Q(
                    prid__remarktype='Reject',
                    prid__rejectuser=user,
                    prid__rejectstage__stage='stage2'
                )
            )
        ).order_by('-latest_reject_datetime', '-id')

        procurements = procurements_qs  # Initialize procurements with procurements_qs
        
        #print('procurements_qs:', procurements_qs)

        try:
            today = datetime.today().date()

            if start_date_str:
                try:
                    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                except ValueError:
                    start_date = None
            else:
                start_date = None

            if end_date_str:
                try:
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                except ValueError:
                    end_date = None
            else:
                end_date = None

            # Apply date filtering logic
            if start_date and end_date:
                procurements = procurements.filter(datetime__date__gte=start_date, datetime__date__lte=end_date)
            elif start_date and not end_date:
                procurements = procurements.filter(datetime__date__gte=start_date, datetime__date__lte=today)
            elif not start_date and end_date:
                procurements = procurements.filter(datetime__date__lte=end_date)
            elif not start_date and not end_date:
                # Default: current + previous month
                first_day_current_month = today.replace(day=1)
                first_day_previous_month = first_day_current_month - relativedelta(months=1)
                procurements = procurements.filter(datetime__date__gte=first_day_previous_month)
        except Exception as e:
            print("Date filtering error:", e)

        # Prepare status list with reject, approval, and modified remarks
        status_list = []

        for procurement in procurements:
            # ####pdb.set_trace()
            remarks = set()
            last_remark = StageProgress.objects.filter(
                procurement_id__procurement_id=procurement.procurement_id
            ).values("rejectstage__stage", "remarktype").last()

            if last_remark and (last_remark["rejectstage__stage"] == "stage2" and last_remark["remarktype"] in ["Reject", "Modified"]):
                procurement.action_performed = True
            else:
                procurement.action_performed = False

            # ✅ Reject
            reject_remarks = StageProgress.objects.filter(
                procurement_id__procurement_id=procurement.procurement_id,
                remarktype="Reject"
            ).values_list("remarktype", flat=True).distinct()
            remarks.update(reject_remarks)

            # ✅ Modified
            modified_remarks = StageProgress.objects.filter(
                procurement_id__procurement_id=procurement.procurement_id,
                remarktype="Modified"
            ).values_list("remarktype", flat=True).distinct()
            remarks.update(modified_remarks)

            # ✅ Stage 5 Approval (latest only)
            latest_stage5 = (
                StageProgress.objects.filter(
                    procurement_id__procurement_id=procurement.procurement_id,
                    stagename__stage="stage5"
                )
                .order_by("-datetime")
                .values_list("remarktype", flat=True)
                .first()
            )
            if latest_stage5 == "Approval":
                remarks.add("Approval")

            procurement.procurement_title = procurement.procurement_title

            status_list.append({
                "procurement_id": procurement.procurement_id,
                "statuses": list(remarks),
            })

            # Check if action was performed at stage 2
            

        # Set procurements variable to final queryset after filtering
        # procurements = procurements_qs

    except Exception as e:
        #print(f"Error in get_reject_ra_procurement_data: {e}")
        procurements = []
        status_list = []
    procurements = sorted(
    procurements,
    key=lambda p: (
        getattr(p, "latest_reject_datetime", None)
        or p.datetime
        or datetime.min
    ),
    reverse=True
    )

    context = {
        "procurements": procurements,
        "status_list": status_list,
    }
    print(context)
    return context





def get_aa_procurement_data(request,user):
    from django.db.models import Max, Q

    try:
        user_reg = UserReg.objects.get(user=user)
        department_obj = user_reg.user_dept

        users = UserReg.objects.filter(
            role__role="IMM",
            user_dept=department_obj
        ).values("emp_id", "user__id", "user__first_name", "user__last_name", "user_dept__dept_name")

        # Get procurement IDs from StageProgress
        stage4_ids = StageProgress.objects.filter(
            stagename__stage="stage4",
            remarktype="Approval"
        ).values_list("procurement_id", flat=True).distinct()

        stage8_ids = StageProgress.objects.filter(
            stagename__stage="stage8",
            remarktype="Negotiation"
        ).values_list("procurement_id", flat=True).distinct()

        immpr = list(stage4_ids) + list(stage8_ids)

        procurements = Procurement.objects.filter(
            aa_user=user,
            id__in=immpr,
            is_draft=False,
        ).annotate(
            latest_valid_stage_datetime=Max(
                'prid__datetime',
                filter=Q(
                    prid__stagename__stage='stage4',
                    prid__remarktype='Approval'
                ) | Q(
                    prid__stagename__stage='stage8',
                    prid__remarktype='Negotiation'
                )
            )
        ).order_by('-latest_valid_stage_datetime', '-id')

        start_date_str = request.GET.get("startDate")
        end_date_str = request.GET.get("endDate")
        status_filter = request.GET.get("statusFilter")

        print("start_date_str:", start_date_str)
        print("end_date_str:", end_date_str)
        print("status_filter:", status_filter)

        # ⭐ Priority 1: If PR IDs exist, override filters
        if "aa_prids" in request.session and request.session["aa_prids"]:
            raw_prids = request.session["aa_prids"]
            print("raw_prids:", raw_prids)

            # ✅ REMOVE ONLY THIS SESSION KEY AFTER USING IT
            request.session.pop("aa_prids", None)

        else:
            print("ra_prids NOT found or empty")
            raw_prids = None

        

        try:
            today = datetime.today().date()

            if start_date_str:
                try:
                    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                except ValueError:
                    start_date = None
            else:
                start_date = None

            if end_date_str:
                try:
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                except ValueError:
                    end_date = None
            else:
                end_date = None

            # Apply date filtering logic
            # ##pdb.set_trace()
            pr_only_list = []
            pr_vendor_pairs = []
            ##pdb.set_trace()
        
            if raw_prids:
                pr_only_list = []
                pr_vendor_pairs = []
                pr_part_pairs = []  # NEW: PR–Particular pairs

                items = [x.strip() for x in raw_prids.split(",") if x.strip()]

                # Categorize each item
                for element in items:

                    # CASE A: Negotiation PR_Particular pair (e.g., PR100_P12)
                    if "_P" in element:
                        pr_id, part_id = element.split("_P")
                        pr_part_pairs.append({
                            "pr_id": pr_id.strip(),
                            "particular_id": int(part_id.strip())
                        })
                        continue

                    # CASE B: Vendor pair (e.g., PR100-5)
                    if "-" in element:
                        pr_id, vendor_id = element.split("-")
                        pr_vendor_pairs.append({
                            "pr_id": pr_id.strip(),
                            "vendor_id": int(vendor_id.strip())
                        })
                        continue

                    # CASE C: PR only
                    pr_only_list.append(element.strip())

                # ==========================================================
                # CASE 1 — ONLY PR IDs (no vendor, no particular)
                # ==========================================================
                if pr_only_list and not pr_vendor_pairs and not pr_part_pairs:
                    procurements = procurements.filter(procurement_id__in=pr_only_list)

                # ==========================================================
                # CASE 2 — PR + PARTICULAR pairs (Negotiation-based)
                # ==========================================================
                elif pr_part_pairs:
                    filtered_negos = []

                    for pair in pr_part_pairs:
                        pr = pair["pr_id"]
                        part = pair["particular_id"]

                        nego = Negotiation.objects.filter(
                            quoted_vendors__csparticular__procurement__procurement_id=pr,
                            quoted_vendors__csparticular_id=part
                        ).first()

                        if nego:
                            filtered_negos.append(nego)

                    if filtered_negos:
                        valid_pr_ids = {
                            nego.quoted_vendors.csparticular.procurement.procurement_id
                            for nego in filtered_negos
                        }
                        procurements = procurements.filter(procurement_id__in=valid_pr_ids)
                        request.vendor_filtered_negotiations = filtered_negos
                    else:
                        procurements = procurements.none()

                # ==========================================================
                # CASE 3 — PR + VENDOR pairs (DPO or PO)
                # ==========================================================
                elif pr_vendor_pairs:
                    filtered_dpos = []
                    filtered_pos = []

                    for pair in pr_vendor_pairs:
                        pr = pair["pr_id"]
                        vendor = pair["vendor_id"]

                        dpo = DPO.objects.filter(
                            procurement__procurement_id=pr,
                            sources__id=vendor
                        ).first()

                        po = Purchase_Order.objects.filter(
                            procurement__procurement_id=pr,
                            draft_po__sources__id=vendor
                        ).first()

                        if dpo:
                            filtered_dpos.append(dpo)
                        if po:
                            filtered_pos.append(po)

                    if filtered_dpos:
                        valid_pr_ids = {dpo.procurement.procurement_id for dpo in filtered_dpos}
                        procurements = procurements.filter(procurement_id__in=valid_pr_ids)
                        request.vendor_filtered_dpos = filtered_dpos

                    elif filtered_pos:
                        valid_pr_ids = {po.procurement.procurement_id for po in filtered_pos}
                        procurements = procurements.filter(procurement_id__in=valid_pr_ids)
                        request.vendor_filtered_pos = filtered_pos

                    else:
                        procurements = procurements.none()

                # ==========================================================
                # CASE 4 — NONE matched / empty
                # ==========================================================
                else:
                    procurements = procurements.none()

            elif start_date and end_date:
                procurements = procurements.filter(datetime__date__gte=start_date, datetime__date__lte=end_date)
            elif start_date and not end_date:
                procurements = procurements.filter(datetime__date__gte=start_date, datetime__date__lte=today)
            elif not start_date and end_date:
                procurements = procurements.filter(datetime__date__lte=end_date)
            elif not start_date and not end_date:
                # Default: current + previous month
                first_day_current_month = today.replace(day=1)
                first_day_previous_month = first_day_current_month - relativedelta(months=1)
                procurements = procurements.filter(datetime__date__gte=first_day_previous_month)
        except Exception as e:
            print("Date filtering error:", e)


        status_list = []
        # # ####pdb.set_trace()
        
        for procurement in procurements:
        
            # Get latest Stage 4 Approval
            latest_stage4 = StageProgress.objects.filter(
                procurement_id=procurement,
                
            ).order_by("-datetime").first()

                

            # Default value
           

            if latest_stage4.stagename.stage=="stage4" and latest_stage4.remarktype=="Approval":
                latest_stage9 = StageProgress.objects.filter(
                    procurement_id=procurement,
                    stagename__stage__in=["stage9","stage6","stage7","stage8","stage10","stage12","stage11"]
                ).order_by("-datetime")
                # ✅ True if:
                # - There is no Stage 9 yet, OR
                # - Stage 4 Approval happened BEFORE Stage 9
                
                if latest_stage9.count():
                    procurement.action_performed = False
                else:
                    procurement.action_performed = True
            else:
                procurement.action_performed = False   

            # 🚫 Always override: Stage 5 Approval or Reject means False
            

            procurement.procurement_title = procurement.procurement_title

            remarks = set()

            # ✅ Reject
            reject_remarks = StageProgress.objects.filter(
                procurement_id__procurement_id=procurement.procurement_id,
                remarktype="Reject"
            ).values_list("remarktype", flat=True).distinct()
            remarks.update(reject_remarks)

            # ✅ Modified
            modified_remarks = StageProgress.objects.filter(
                procurement_id__procurement_id=procurement.procurement_id,
                remarktype="Modified"
            ).values_list("remarktype", flat=True).distinct()
            remarks.update(modified_remarks)

            # ✅ Stage 5 Approval (latest only)
            latest_stage5 = (
                StageProgress.objects.filter(
                    procurement_id__procurement_id=procurement.procurement_id,
                    stagename__stage="stage5"
                )
                .order_by("-datetime")
                .values_list("remarktype", flat=True)
                .first()
            )
            if latest_stage5 == "Approval":
                remarks.add("Approval")

            status_list.append({
                "procurement_id": procurement.procurement_id,
                "statuses": list(remarks)
            })


    except Exception as e:
        print("Error in get_aa_procurement_data:", e)
        procurements = []
        users = []
        status_list = []

    # ⭐ Fix ordering: latest procurement ID must always appear on top
    procurements = sorted(
        procurements,
        key=lambda p: (
            p.latest_valid_stage_datetime or p.datetime or datetime.min
        ),
        reverse=True
    )



    return {
        "procurements": procurements,
        "user_list": users,
        "status_list": status_list,
    }


# def get_indentor_procurement_subdata(request,user):
    
#     try:
#         user_reg = UserReg.objects.get(user=user)

#         # Step 1: Get PR Raised IDs
#         immpr = pd.DataFrame(
#             StageProgress.objects.filter(
#                 stagename__stage="stage1", remarktype="PR_Raised",
#             ).values("procurement_id__procurement_id")
#         ).drop_duplicates(subset=["procurement_id__procurement_id"])["procurement_id__procurement_id"].to_list()

#         # Step 2: Get query params from request
#         start_date_str = request.GET.get("startDate")
#         end_date_str = request.GET.get("endDate")
#         status_filter = request.GET.get("statusFilter")

#         #print("start_date_str:", start_date_str)
#         #print("end_date_str:", end_date_str)
#         #print("status_filter:", status_filter)

#         # Step 3: Initial procurement queryset
#         procurements = Procurement.objects.filter(
#             procurement_id__in=immpr, user=user, is_draft=False, modificationpr=False
#         ).annotate(
#             latest_stage7_cst_modified_datetime=Max(
#                 'prid__datetime',
#                 filter=Q(
#                     Q(prid__stagename__stage='stage7') | Q(prid__stagename__stage='stage1'),
#                     prid__remarktype__in=['CST', 'PR_Raised']
#                 )
#             )
#         ).order_by('-latest_stage7_cst_modified_datetime', '-id')
#         # ##pdb

#         # Step 4: Apply date filters (after queryset is built)
#         # if start_date_str:
#         #     try:
#         #         start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
#         #         procurements = procurements.filter(datetime__date__gte=start_date)
#         #     except ValueError:
#         #         pass  
#         # if end_date_str:
#         #     try:
#         #         end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
#         #         procurements = procurements.filter(datetime__date__lte=end_date)
#         #     except ValueError:
#         #         pass
#         # # If no date filters are applied by user, show current & previous month
#         # if not start_date_str and not end_date_str:
#         #     today = datetime.today()
#         #     first_day_current_month = today.replace(day=1)
#         #     first_day_previous_month = first_day_current_month - relativedelta(months=1)
#         #     procurements = procurements.filter(datetime__date__gte=first_day_previous_month)
#         # #pdb.set_trace
#         try:
#             today = datetime.today().date()

#             if start_date_str:
#                 try:
#                     start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
#                 except ValueError:
#                     start_date = None
#             else:
#                 start_date = None

#             if end_date_str:
#                 try:
#                     end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
#                 except ValueError:
#                     end_date = None
#             else:
#                 end_date = None

#             # Filtering logic
#             if start_date and end_date:
#                 procurements = procurements.filter(datetime__date__gte=start_date, datetime__date__lte=end_date)
#             elif start_date and not end_date:
#                 procurements = procurements.filter(datetime__date__gte=start_date, datetime__date__lte=today)
#             elif not start_date and end_date:
#                 procurements = procurements.filter(datetime__date__lte=end_date)
#             elif not start_date and not end_date:
#                 # Default: current + previous month
#                 first_day_current_month = today.replace(day=1)
#                 first_day_previous_month = first_day_current_month - relativedelta(months=1)
#                 procurements = procurements.filter(datetime__date__gte=first_day_previous_month)
#         except Exception as e:
#             print("Date filtering error:", e)



        

#         # Step 5: Add extra fields
#         for procurement in procurements:
#             checkmsg = StageProgress.objects.filter(
#                 procurement_id__procurement_id=procurement.procurement_id
#             ).order_by('-id').values("stagename__stage", "remarktype").first()

#             cs_entry = CompartiveStatementPR.objects.filter(
#                 pro_id__procurement_id=procurement.procurement_id
#             ).last()

#             if (
#                 checkmsg and
#                 checkmsg["stagename__stage"] == "stage7" and
#                 checkmsg["remarktype"] in ["CST_approval", "Modified"] and
#                 cs_entry and
#                 cs_entry.send_to == "Indentor"
#             ):
#                 procurement.action_performed = True
#             else:
#                 procurement.action_performed = False


#             # Add procurement_title attribute (already exists on model, just to be sure)
#             procurement.procurement_title = procurement.procurement_title

#         # Step 6: Status filtering
#         # Step 6: Status filtering
#         status_list = []
#         final_procurements = []

#         for procurement in procurements:
#             remarks = set()

#             # ✅ Reject
#             reject_remarks = StageProgress.objects.filter(
#                 procurement_id__procurement_id=procurement.procurement_id,
#                 remarktype="Reject"
#             ).values_list("remarktype", flat=True).distinct()
#             remarks.update(reject_remarks)

#             # ✅ Modified
#             modified_remarks = StageProgress.objects.filter(
#                 procurement_id__procurement_id=procurement.procurement_id,
#                 remarktype="Modified"
#             ).values_list("remarktype", flat=True).distinct()
#             remarks.update(modified_remarks)

#             # ✅ Stage 5 Approval (latest only)
#             latest_stage5 = (
#                 StageProgress.objects.filter(
#                     procurement_id__procurement_id=procurement.procurement_id,
#                     stagename__stage="stage5"
#                 )
#                 .order_by("-datetime")
#                 .values_list("remarktype", flat=True)
#                 .first()
#             )
#             if latest_stage5 == "Approval":
#                 remarks.add("Approval")

#             # Build status_list entry
#             status_list.append({
#                 "procurement_id": procurement.procurement_id,
#                 "statuses": list(remarks)
#             })

#             # ✅ Apply status filter
#             if status_filter and status_filter != "all":
#                 if status_filter in remarks:
#                     final_procurements.append(procurement)
#             else:
#                 final_procurements.append(procurement)
                

#     except Exception as e:
#         #print("Error in get_indentor_procurement_data:", e)
#         procurements = []
#         status_list = []
#         final_procurements = []

#     return {
#         "procurements": final_procurements,
#         "status_list": status_list
#     }
def get_indentor_procurement_subdata(request, user):

    try:
        user_reg = UserReg.objects.get(user=user)

        # -----------------------------
        # STEP 1: Fetch PR Raised IDs
        # -----------------------------
        immpr = (
            StageProgress.objects.filter(
                stagename__stage="stage1",
                remarktype="PR_Raised",
            )
            .values_list("procurement_id__procurement_id", flat=True)
            .distinct()
        )

        # -----------------------------
        # STEP 2: Build initial queryset
        # -----------------------------
        procurements_qs = Procurement.objects.filter(
            procurement_id__in=immpr,
            user=user,
            is_draft=False,
            modificationpr=False
        ).annotate(
            latest_stage7_cst_modified_datetime=Max(
                'prid__datetime',
                filter=Q(
                    Q(prid__stagename__stage='stage7') |
                    Q(prid__stagename__stage='stage1'),
                    prid__remarktype__in=['CST', 'PR_Raised']
                )
            )
        )

        procurements = procurements_qs  # Assign for filtering

        # -----------------------------
        # STEP 3 — DATE FILTERING
        # -----------------------------
        # #pdb.set_trace()
        start_date_str = request.GET.get("startDate")
        end_date_str = request.GET.get("endDate")
        status_filter = request.GET.get("statusFilter")
        if "submitted_prids" in request.session and request.session["submitted_prids"]:
            raw_prids = request.session["submitted_prids"]
            print("raw_prids:", raw_prids)

            # ✅ REMOVE ONLY THIS SESSION KEY AFTER USING IT
            request.session.pop("submitted_prids", None)
            print("Removed submitted_prids from session")
        else:
            print("submitted_prids NOT found or empty")
            raw_prids = None
        today = datetime.today().date()

        # Safe date parsing
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
        except:
            start_date = None

        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None
        except:
            end_date = None

        # Apply filters
        pr_only_list = []
        pr_vendor_pairs = []
        # ##pdb.set_trace()

        # ##pdb.set_trace()
        # if raw_prids:
        #     pr_only_list = []
        #     pr_vendor_pairs = []
        #     pr_part_pairs = []  # NEW: PR–Particular pairs

        #     items = [x.strip() for x in raw_prids.split(",") if x.strip()]

        #     # Categorize each item
        #     for element in items:

        #         # CASE A: Negotiation PR_Particular pair (e.g., PR100_P12)
        #         if "_P" in element:
        #             pr_id, part_id = element.split("_P")
        #             pr_part_pairs.append({
        #                 "pr_id": pr_id.strip(),
        #                 "particular_id": int(part_id.strip())
        #             })
        #             continue

        #         # CASE B: Vendor pair (e.g., PR100-5)
        #         if "-" in element:
        #             pr_id, vendor_id = element.split("-")
        #             pr_vendor_pairs.append({
        #                 "pr_id": pr_id.strip(),
        #                 "vendor_id": int(vendor_id.strip())
        #             })
        #             continue

        #         # CASE C: PR only
        #         pr_only_list.append(element.strip())

        #     # ==========================================================
        #     # CASE 1 — ONLY PR IDs (no vendor, no particular)
        #     # ==========================================================
        #     if pr_only_list and not pr_vendor_pairs and not pr_part_pairs:
        #         procurements = procurements.filter(procurement_id__in=pr_only_list)

        #     # ==========================================================
        #     # CASE 2 — PR + PARTICULAR pairs (Negotiation-based)
        #     # ==========================================================
        #     elif pr_part_pairs:
        #         filtered_negos = []

        #         for pair in pr_part_pairs:
        #             pr = pair["pr_id"]
        #             part = pair["particular_id"]

        #             nego = Negotiation.objects.filter(
        #                 quoted_vendors__csparticular__procurement__procurement_id=pr,
        #                 quoted_vendors__csparticular_id=part
        #             ).first()

        #             if nego:
        #                 filtered_negos.append(nego)

        #         if filtered_negos:
        #             valid_pr_ids = {
        #                 nego.quoted_vendors.csparticular.procurement.procurement_id
        #                 for nego in filtered_negos
        #             }
        #             procurements = procurements.filter(procurement_id__in=valid_pr_ids)
        #             request.vendor_filtered_negotiations = filtered_negos
        #         else:
        #             procurements = procurements.none()

        #     # ==========================================================
        #     # CASE 3 — PR + VENDOR pairs (DPO or PO)
        #     # ==========================================================
        #     elif pr_vendor_pairs:
        #         filtered_dpos = []
        #         filtered_pos = []

        #         for pair in pr_vendor_pairs:
        #             pr = pair["pr_id"]
        #             vendor = pair["vendor_id"]

        #             dpo = DPO.objects.filter(
        #                 procurement__procurement_id=pr,
        #                 sources__id=vendor
        #             ).first()

        #             po = Purchase_Order.objects.filter(
        #                 procurement__procurement_id=pr,
        #                 draft_po__sources__id=vendor
        #             ).first()

        #             if dpo:
        #                 filtered_dpos.append(dpo)
        #             if po:
        #                 filtered_pos.append(po)

        #         if filtered_dpos:
        #             valid_pr_ids = {dpo.procurement.procurement_id for dpo in filtered_dpos}
        #             procurements = procurements.filter(procurement_id__in=valid_pr_ids)
        #             request.vendor_filtered_dpos = filtered_dpos

        #         elif filtered_pos:
        #             valid_pr_ids = {po.procurement.procurement_id for po in filtered_pos}
        #             procurements = procurements.filter(procurement_id__in=valid_pr_ids)
        #             request.vendor_filtered_pos = filtered_pos

        #         else:
        #             procurements = procurements.none()

        #     # ==========================================================
        #     # CASE 4 — NONE matched / empty
        #     # ==========================================================
        #     else:
        #         procurements = procurements.none()
        if raw_prids:
            # If raw_prids is provided, filter by those PR IDs only
            pr_ids = [pr_id.strip() for pr_id in raw_prids.split(",") if pr_id.strip()]
            procurements = procurements.filter(procurement_id__in=pr_ids)
        elif start_date and end_date:
            procurements = procurements.filter(datetime__date__gte=start_date,
                                               datetime__date__lte=end_date)
        elif start_date and not end_date:
            procurements = procurements.filter(datetime__date__gte=start_date,
                                               datetime__date__lte=today)
        elif not start_date and end_date:
            procurements = procurements.filter(datetime__date__lte=end_date)
        else:
            # Default → current + previous month
            first_day_current = today.replace(day=1)
            prev_month_first = first_day_current - relativedelta(months=1)
            procurements = procurements.filter(datetime__date__gte=prev_month_first)

        # -----------------------------
        # STEP 4 — ADD EXTRA FIELDS
        # -----------------------------
        for procurement in procurements:
            # Last stage
            checkmsg = (
                StageProgress.objects.filter(procurement_id__procurement_id=procurement.procurement_id)
                .order_by('-id')
                .values("stagename__stage", "remarktype")
                .first()
            )

            cs_entry = (
                CompartiveStatementPR.objects.filter(
                    pro_id__procurement_id=procurement.procurement_id
                ).last()
            )

            if (
                checkmsg and
                checkmsg["stagename__stage"] == "stage7" and
                checkmsg["remarktype"] in ["CST_approval", "Modified"] and
                cs_entry and
                cs_entry.send_to == "Indentor"
            ):
                procurement.action_performed = True
            else:
                procurement.action_performed = False

        # -----------------------------
        # STEP 5 — BUILD STATUS LIST
        # -----------------------------
        status_list = []
        filtered_procurements = []

        for procurement in procurements:
            remarks = set()

            # Reject
            remarks.update(
                StageProgress.objects.filter(
                    procurement_id__procurement_id=procurement.procurement_id,
                    remarktype="Reject"
                ).values_list("remarktype", flat=True)
            )

            # Modified
            remarks.update(
                StageProgress.objects.filter(
                    procurement_id__procurement_id=procurement.procurement_id,
                    remarktype="Modified"
                ).values_list("remarktype", flat=True)
            )

            # Stage 5 Approval
            latest_stage5 = (
                StageProgress.objects.filter(
                    procurement_id__procurement_id=procurement.procurement_id,
                    stagename__stage="stage5"
                )
                .order_by("-datetime")
                .values_list("remarktype", flat=True)
                .first()
            )
            if latest_stage5 == "Approval":
                remarks.add("Approval")

            status_list.append({
                "procurement_id": procurement.procurement_id,
                "statuses": list(remarks)
            })

            # Apply status filter
            if status_filter and status_filter != "All":
                if status_filter in remarks:
                    filtered_procurements.append(procurement)
            else:
                filtered_procurements.append(procurement)
            print(status_filter, remarks, filtered_procurements, procurement)

        # -----------------------------
        # STEP 6 — FINAL SORT (critical)
        # -----------------------------
        # Stable ordering for SQLite + PostgreSQL
        # ⭐ FIX: Sort by latest PR ID first, then by latest stage datet    ime
        final_procurements = sorted(
            filtered_procurements,
            key=lambda p: (
                getattr(p, "latest_stage7_cst_modified_datetime", None) or p.datetime or datetime.min
            ),
            reverse=True
        )


    except Exception as e:
        print("Error in get_indentor_procurement_subdata:", e)
        final_procurements = []
        status_list = []

    return {
        "procurements": final_procurements,
        "status_list": status_list
    }


# def get_enquiry_procurement_subdata(user):
#     try:
#         user_reg = UserReg.objects.get(user=user)
#         roles = user_reg.role.all()
#         role_names = [role.role for role in roles]

#         # Ensure user is IMM
#         if "IMM" not in role_names:
#             return {"procurements": []}

#         # Get procurement IDs with stage5 Approval
#         immpr = pd.DataFrame(
#             StageProgress.objects.filter(stagename__stage="stage5", remarktype="Approval")
#             .values("procurement_id__procurement_id")
#         ).drop_duplicates(subset=["procurement_id__procurement_id"])["procurement_id__procurement_id"].to_list()

#         # Fetch procurements for IMM user
#         procurements = Procurement.objects.filter(
#             procurement_id__in=immpr,
#             imm_user=user
#         ).annotate(
#             latest_stage_datetime=Max(
#                 'prid__datetime',
#                 filter=Q(prid__stagename__stage='stage5', prid__remarktype='Approval')
#             )
#         ).order_by('-latest_stage_datetime', '-id')

#         # Annotate each with action_performed
#         for procurement in procurements:
#             checkmsg = StageProgress.objects.filter(
#                 procurement_id__procurement_id=procurement.procurement_id
#             ).values("stagename__stage", "remarktype").last()

#             procurement.action_performed = (
#                 checkmsg and checkmsg["stagename__stage"] == "stage5" and checkmsg["remarktype"] == "Approval"
#             )

#     except Exception as e:
#         #print("Error in get_imm_procurement_subdata:", e)
#         procurements = []

#     return {"procurements": procurements}

# def get_enquiry_procurement_subdata(user):
#     try:
#         # #pdb
#         # user = request.user
#         user_reg = UserReg.objects.get(user=user)
#         roles = user_reg.role.all()
#         role_names = [role.role for role in roles]
#         #print("Roles:", role_names)

#         imm_user = user

#         if "IMM" not in role_names:
#             #print("User is not IMM")
#             return {"procurements": []}

#         # Get procurement IDs with stage5 Approval
#         immpr = StageProgress.objects.filter(
#             stagename__stage="stage5", remarktype="Approval"
#         ).values_list("procurement_id__procurement_id", flat=True).distinct()
#         immpr = list(immpr)
#         #print("Stage5 Approved procurement IDs:", immpr)

#         if "Indentor" in role_names:
#             proc_approved = Procurement.objects.filter(procurement_id__in=immpr,is_draft=False)
#             proc_raised = Procurement.objects.filter(user=user)
#             #print("Procurements stage5 approved + imm_user:", proc_approved.count())
#             #print("Procurements raised by user:", proc_raised.count())

#             procurements = (proc_approved | proc_raised).distinct().annotate(
#                 latest_stage_datetime=Max(
#                     'prid__datetime',
#                     filter=Q(prid__stagename__stage='stage5', prid__remarktype='Approval')
#                 )
#             ).order_by('-latest_stage_datetime', '-id')

#         else:
#             procurements = Procurement.objects.filter(
#                 procurement_id__in=immpr
#             ).annotate(
#                 latest_stage_datetime=Max(
#                     'prid__datetime',
#                     filter=Q(prid__stagename__stage='stage5', prid__remarktype='Approval')
#                 )
#             ).order_by('-latest_stage_datetime', '-id')


#         # for procurement in procurements:
#         #     # Fetch all progress records in order
#         #     all_progress = StageProgress.objects.filter(
#         #         procurement_id__procurement_id=procurement.procurement_id
#         #     ).order_by('datetime')

#         #     # Find the first stage5 Approval
#         #     first_stage5 = None
#         #     for progress in all_progress:
#         #         if progress.stagename.stage == "stage5" and progress.remarktype == "Approval":
#         #             first_stage5 = progress
#         #             break

#         #     # Get the latest stage progress
#         #     latest_stage = all_progress.last()

#         #     # Save latest stage info to display (optional)
#         #     procurement.checkmsg = {
#         #         "stagename__stage": latest_stage.stagename.stage if latest_stage else None,
#         #         "remarktype": latest_stage.remarktype if latest_stage else None
#         #     }

#         #     # Set action_performed based on your rule
#         #     if (
#         #         first_stage5 and latest_stage and
#         #         first_stage5.id == latest_stage.id
#         #     ):
#         #         procurement.action_performed = True
#         #     else:
#         #         procurement.action_performed = False
#         for procurement in procurements:
#             # Fetch all progress records in order
#             all_progress = StageProgress.objects.filter(
#                 procurement_id__procurement_id=procurement.procurement_id
#             ).order_by('datetime')

#             # Find the first stage5 Approval
#             first_stage5 = None
#             for progress in all_progress:
#                 if progress.stagename.stage == "stage5" and progress.remarktype == "Approval":
#                     first_stage5 = progress
#                     break

#             # Get the latest stage progress
#             latest_stage = all_progress.last()

#             # Save latest stage info to display (optional)
#             procurement.checkmsg = {
#                 "stagename__stage": latest_stage.stagename.stage if latest_stage else None,
#                 "remarktype": latest_stage.remarktype if latest_stage else None
#             }

#             # Only assign action_performed if user is imm_user
#             if procurement.imm_user == user:
#                 if (
#                     first_stage5 and latest_stage and
#                     first_stage5.id == latest_stage.id
#                 ):
#                     procurement.action_performed = True
#                 else:
#                     procurement.action_performed = False
#             else:
#                 procurement.action_performed = False  # Or skip this line if you want it to be undefined


#         #print(f"Total procurements returned: {procurements.count()}")

#     except Exception as e:
#         #print("Error in get_imm_procurement_subdata:", e)
#         procurements = []

#     return {"procurements": procurements,'imm_user':imm_user}


def get_enquiry_procurement_subdata(request, user):
    try:
        # Get user roles
        user_reg = UserReg.objects.get(user=user)
        roles = user_reg.role.all()
        role_names = [role.role for role in roles]
        print("Roles ramya sistla:", role_names)

        imm_user = user

        # Allow both IMM and Purchase Assistant roles
        allowed_roles = {"IMM", "Purchase Assistant"}
        if not any(role in role_names for role in allowed_roles):
            #print("User does not have permission (Not IMM or Purchase Assistant)")
            return {"procurements": []}
        

        # Get procurement IDs with stage5 Approval
        # 1. Get all stage5-approved original procurement IDs
        
    

        # 2. Start with the original procurements
        immpr1 = StageProgress.objects.filter(
            stagename__stage="stage5", remarktype="Approval"
        ).values_list("procurement_id", flat=True).distinct()
        immpr1 = list(immpr1)

        from django.db.models import OuterRef, Subquery
        latest_subquery = ModifiedPr.objects.filter(procurement_id=OuterRef('procurement_id')).order_by('-datetime')
        latest_per_procurement = ModifiedPr.objects.filter(procurement_id__in=immpr1,id=Subquery(latest_subquery.values('id')[:1]))
        immpr = []
        for i in immpr1:
            myvar = False
            for k in latest_per_procurement:
                if k.procurement.id == i:
                    myvar = True
                    if k.modifiedpr.is_delivered == False and k.modifiedpr.pr_events=='Purchase_order':
                        immpr.append(k.procurement.id)
                    break
            if myvar == False:
                pr = Procurement.objects.get(id=i)
                if pr.is_delivered == False and pr.pr_events=='Purchase_order':
                    immpr.append(i)
        

        #print("Stage5 Approved procurement IDs:", immpr)


        approveusers = UserReg.objects.filter(
            Q(role__role="Purchase Assistant")
        ).values(
            "emp_id", "user__id", "user__first_name", "user__last_name", "user_dept__dept_name"
        )

        user_list = [
            {
                "emp_id": u["emp_id"],
                "first_name": u["user__first_name"],
                "last_name": u["user__last_name"],
                "full_name": f"{u['user__first_name']} {u['user__last_name']}"
            }
            for u in approveusers
        ]

        #check is_delivered condition

        
    
        # If user is also Indentor, include procurements they raised
        if "Indentor" in role_names:

            proc_approved = Procurement.objects.filter(id__in=immpr, is_draft=False)
            proc_raised = Procurement.objects.filter(user=user)
            #print("Procurements stage5 approved:", proc_approved.count())
            #print("Procurements raised by user:", proc_raised.count())

            procurements = (proc_approved | proc_raised).distinct().annotate(
                latest_stage_datetime=Max(
                    'prid__datetime',
                    filter=Q(prid__stagename__stage='stage5', prid__remarktype='Approval')
                )
            ).order_by('-latest_stage_datetime', '-id')
        else:
            
            procurements = Procurement.objects.filter(
                id__in=immpr, is_draft=False
            ).annotate(
                latest_stage_datetime=Max(
                    'prid__datetime',
                    filter=Q(prid__stagename__stage='stage5', prid__remarktype='Approval')
                )
            ).order_by('-latest_stage_datetime', '-id')

        # Handle date filtering
        # ####pdb.set_trace()
        start_date_str = request.GET.get("startDate")
        end_date_str = request.GET.get("endDate")
        status_filter = request.GET.get("statusFilter")
        ##pdb.set_trace()
        if "imm_prids" in request.session and request.session["imm_prids"]:
            raw_prids = request.session["imm_prids"]
            print("raw_prids:", raw_prids)

            # ✅ REMOVE ONLY THIS SESSION KEY AFTER USING IT
            request.session.pop("imm_prids", None)

        else:
            print("imm_prids NOT found or empty")
            raw_prids = None
        #print("start_date_str:", start_date_str)
        #print("end_date_str:", end_date_str)
        #print("status_filter:", status_filter)
        try:
            today = datetime.today().date()

            # Parse start and end dates
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None

            # Apply date filtering logic to procurements
            if raw_prids:
                prids_list = [p.strip() for p in raw_prids.split(",") if p.strip()]
                procurements = procurements.filter(procurement_id__in=prids_list)
            elif start_date and end_date:
                procurements = procurements.filter(datetime__date__gte=start_date, datetime__date__lte=end_date)
            elif start_date and not end_date:
                procurements = procurements.filter(datetime__date__gte=start_date, datetime__date__lte=today)
            elif not start_date and end_date:
                procurements = procurements.filter(datetime__date__lte=end_date)
            elif not start_date and not end_date:
                # Default: current + previous month
                first_day_current_month = today.replace(day=1)
                first_day_previous_month = first_day_current_month - relativedelta(months=1)
                procurements = procurements.filter(datetime__date__gte=first_day_previous_month)

        except Exception as e:
            print("Date filtering error:", e)
 
        # Process each procurement for hightlights
        for procurement in procurements:
            # Fetch all progress records in order
            all_progress = StageProgress.objects.filter(
                procurement_id__procurement_id=procurement.procurement_id
            ).order_by('datetime')

            # Check for any enquiry_approval remarks (case-insensitive)
            has_enquiry_approval = all_progress.filter(remarktype__iexact="enquiry_approval").exists()

            # Find the first stage5 Approval
            first_stage5 = None
            for progress in all_progress:
                if progress.stagename.stage == "stage5" and progress.remarktype == "Approval":
                    first_stage5 = progress
                    break

            # Get the latest stage progress
            latest_stage = all_progress.last()

            # Save latest stage info to display (optional)
            procurement.checkmsg = {
                "stagename__stage": latest_stage.stagename.stage if latest_stage else None,
                "remarktype": latest_stage.remarktype if latest_stage else None
            }

            # Always false if enquiry_approval is present
            if has_enquiry_approval:
                procurement.action_performed = False
                continue  # Skip remaining logic for this procurement

            # Default to False
            procurement.action_performed = False

            # Assign action_performed based on role and latest stage info
            if procurement.imm_user == user or "Purchase Assistant" in role_names or "IMM" in role_names:
                if first_stage5 and latest_stage and first_stage5.id == latest_stage.id:
                    procurement.action_performed = True
                else:
                    remarktype = latest_stage.remarktype.lower().strip() if latest_stage and latest_stage.remarktype else ""

                    if "Purchase Assistant" in role_names:
                        if remarktype == "enquiry_return":
                            procurement.action_performed = True
                        elif remarktype in ["enquiry_generated", "enquiry_modified"]:
                            procurement.action_performed = False

                    if "IMM" in role_names:
                        if remarktype == "enquiry_approval":
                            procurement.action_performed = False
                        else:
                            procurement.action_performed = True
            else:
                procurement.action_performed = False


        #print(f"Total procurements returned: {procurements.count()}")

    except Exception as e:
        #print("Error in get_enquiry_procurement_subdata:", e)
        procurements = []

    # ⭐ Stable ordering across PostgreSQL + SQLite
    # ⭐ Fix: latest procurement ID should always appear on top
    procurements = sorted(
        procurements,
        key=lambda p: (
            p.latest_stage_datetime or p.datetime or datetime.min
        ),
        reverse=True
    )



    return {
        "procurements": procurements,
        "imm_user": imm_user,
        "user": user,
        "roles": role_names,
        "approveusers": user_list,
    }

def get_rejected_procurements(request,user):
    # #pdb
    try:

        # Get all procurement IDs where the last remark was a rejection to stage1
        stage1_rejections = StageProgress.objects.filter(
            rejectstage__stage="stage1",
            remarktype="Reject",
            stagename__stage__in=["stage2", "stage3", "stage4", "stage5"],
            procurement_id__user=user  # Only get rejections for this indentor
        ).values_list("procurement_id__procurement_id", flat=True)

        # Remove duplicates
        returned_to_stage1 = list(set(stage1_rejections))

        # Get all procurement objects based on those returned to stage1
        rejected_prs = Procurement.objects.filter(
            procurement_id__in=returned_to_stage1
        ).annotate(
            latest_reject_datetime=Max(
                'prid__datetime',
                filter=Q(
                    prid__remarktype='Reject',
                    prid__rejectstage__stage='stage1'
                )
            )
        ).order_by('-latest_reject_datetime', '-id')

        # Get query parameters for date and status filters
        start_date_str = request.GET.get("startDate")
        end_date_str = request.GET.get("endDate")
        status_filter = request.GET.get("statusFilter")

        #print("start_date_str:", start_date_str)
        #print("end_date_str:", end_date_str)
        #print("status_filter:", status_filter)

        try:
            today = datetime.today().date()

            # Parse start and end dates
            if start_date_str:
                try:
                    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                except ValueError:
                    start_date = None
            else:
                start_date = None

            if end_date_str:
                try:
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                except ValueError:
                    end_date = None
            else:
                end_date = None

            # Apply date filtering logic to `rejected_prs`
            if start_date and end_date:
                rejected_prs = rejected_prs.filter(datetime__date__gte=start_date, datetime__date__lte=end_date)
            elif start_date and not end_date:
                rejected_prs = rejected_prs.filter(datetime__date__gte=start_date, datetime__date__lte=today)
            elif not start_date and end_date:
                rejected_prs = rejected_prs.filter(datetime__date__lte=end_date)
            elif not start_date and not end_date:
                # Default: current + previous month
                first_day_current_month = today.replace(day=1)
                first_day_previous_month = first_day_current_month - relativedelta(months=1)
                rejected_prs = rejected_prs.filter(datetime__date__gte=first_day_previous_month)

        except Exception as e:
            print("Date filtering error:", e)

        # Add action_performed flag for each procurement
        for procurement in rejected_prs:
            last_stage = StageProgress.objects.filter(
                procurement_id__procurement_id=procurement.procurement_id
            ).order_by('-datetime').first()  # Get the latest StageProgress object

            procurement.procurement_title = procurement.procurement_title

            # Set action_performed flag based on last rejection stage
            if last_stage and last_stage.remarktype == "Reject":
                try:
                    stage_num = int(last_stage.stagename.stage.replace('stage', ''))
                except (ValueError, AttributeError):
                    stage_num = 999  # Fallback if format is unexpected

                if stage_num <= 5 and last_stage.rejectuser == user:
                    # Only mark action_performed True if last rejection stage is <= stage5
                    # and the rejectuser is the current user
                    procurement.action_performed = True
                else:
                    procurement.action_performed = False
            else:
                procurement.action_performed = False

    except Exception as e:
        #print("Error in get_rejected_procurements:", e)
        rejected_prs = []

    return rejected_prs


# def get_enquiry_procurement_data(user):
#     try:
#         user_reg = UserReg.objects.get(user=user)
#         roles = user_reg.role.all()
#         role_names = [role.role for role in roles]

#         if "IMM" not in role_names:
#             return {"procurements": []}

#         # Step 1: Get procurement IDs for stage5 Approval
#         immpr = pd.DataFrame(
#             StageProgress.objects.filter(stagename__stage="stage5", remarktype="Approval")
#             .values("procurement_id__procurement_id")
#         ).drop_duplicates(subset=["procurement_id__procurement_id"])["procurement_id__procurement_id"].to_list()

#         # Step 2: Fetch procurements
#         procurements = Procurement.objects.filter(procurement_id__in=immpr, imm_user=user).annotate(
#             latest_stage_datetime=Max(
#                 'prid__datetime',
#                 filter=Q(prid__stagename__stage='stage5', prid__remarktype='Approval')
#             )
#         ).order_by('-latest_stage_datetime', '-id')

#         # Step 3: Annotate action_performed flag
#         for procurement in procurements:
#             checkmsg = StageProgress.objects.filter(
#                 procurement_id__procurement_id=procurement.procurement_id
#             ).values("stagename__stage", "remarktype").last()

#             if checkmsg and checkmsg["stagename__stage"] == "stage5" and checkmsg["remarktype"] == "Approval":
#                 procurement.action_performed = True
#             else:
#                 procurement.action_performed = False

#     except Exception as e:
#         #print("Error in get_imm_procurement_data:", e)
#         procurements = []

#     return {"procurements": procurements}


