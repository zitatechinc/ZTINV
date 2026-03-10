from django.views import View
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from .forms import ThemeModelForm, AppSettingsModelForm
from .models import Themes, AppSettings
from core.views import BaseCRUDView, ThemeBaseCrudView
from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from .utils import resolve_fk
from django.db.models import Q   # ✅ ADDED


class ThemesCRUDView(ThemeBaseCrudView):
    model = Themes
    form_class = ThemeModelForm
    

    def get_extra_context(self):
        return {
            
        }

def index(request):
    return HttpResponse("Hello, world")

class AppSettingsCRUDView(BaseCRUDView):
    model = AppSettings
    form_class = AppSettingsModelForm


    def get_extra_context(self):
        return {
            
        }

class AuditLogCRUDView(BaseCRUDView):
    model = LogEntry
    form_class = None

    # Used directly by your existing dropdown
    FieldList = (
        ("entity", "Entity"),
        ("user", "User"),
        ("name","AuditName"),
        ("code","AuditCode"),
        # ("column", "Column"),
        # ("value", "Old / New Value"),
        ("action", "Action"),
    )

    def get_queryset(self):
        """
        DB-level filtering wherever possible
        """
        qs = LogEntry.objects.select_related(
            "actor", "content_type"
        ).order_by("-timestamp")

        keyword = self.request.GET.get("Keyword", "").strip().lower()
        field = self.request.GET.get("FieldName")

        if keyword:
            if field == "entity":
                qs = qs.filter(content_type__model__icontains=keyword)

            elif field == "user":
                qs = qs.filter(actor__username__icontains=keyword)

            elif field == "action":
                qs = qs.filter(action__icontains=keyword)

            # column / value → handled later (Python)
        return qs

    def get_extra_context(self):
        keyword = self.request.GET.get("Keyword", "").strip().lower()
        field = self.request.GET.get("FieldName")

        queryset = self.get_queryset()

        logs = []

        # Pagination first (important)
        paginator = Paginator(queryset, 10)
        page_number = self.request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        for entry in page_obj:
            changes = entry.changes_dict or {}

            # ✅ Get actual model class
            model_class = entry.content_type.model_class()

            audit_name = None
            audit_code = None

            if model_class:
                try:
                    instance = model_class.objects.filter(pk=entry.object_id).first()
                    if instance:
                        audit_name = getattr(instance, "audit_name", None)
                        audit_code = getattr(instance, "audit_code", None)
                except Exception:
                    pass

            for column, (old, new) in changes.items():

                # Python-level filtering only where unavoidable
                if keyword:
                    if field == "column" and keyword not in column.lower():
                        continue

                    if field == "value" and not (
                        keyword in str(old).lower()
                        or keyword in str(new).lower()
                    ):
                        continue
                # print(dir(entry))
                logs.append({
                    "EntityName": entry.content_type.model,
                    "RowID": entry.object_id,
                    "ColumnName": column,
                    "AuditName": audit_name,
                    "AuditCode": audit_code,
                    "OldValue": old,
                    "NewValue": new,
                    "Action": entry.get_action_display(),
                    "User": entry.actor.get_full_name() or entry.actor.get_username() if entry.actor else None,
                    "Timestamp": entry.timestamp,
                })

        return {
            "FieldList": self.FieldList,
            "FieldName": field,
            "Keyword": self.request.GET.get("Keyword",""),
            "page_obj": page_obj,
            "object_list": logs,
        }


# class AuditLogCRUDView(BaseCRUDView):
#     model = LogEntry
#     form_class = None

#     def get_extra_context(self):
#         logs = []
#         keyword = self.request.GET.get('keyword', '').strip().lower()  # get search keyword

#         # Fetch all log entries (latest first)
#         entries = LogEntry.objects.select_related("actor", "content_type").order_by("-timestamp")

#         # Filter keyword in Python since changes_dict is a dict
#         filtered_entries = []
#         for entry in entries:
#             # Search in entity, user, or changes_dict values
#             if keyword:
#                 entity_match = keyword in entry.content_type.model.lower()
#                 user_match = entry.actor and keyword in entry.actor.username.lower()
#                 changes_match = any(
#                     keyword in str(v[0]).lower() or keyword in str(v[1]).lower()
#                     for v in (entry.changes_dict or {}).values()
#                 )

#                 if entity_match or user_match or changes_match:
#                     filtered_entries.append(entry)
#             else:
#                 filtered_entries.append(entry)

#         # Pagination
#         page_number = self.request.GET.get("page", 1)
#         paginator = Paginator(filtered_entries, 10)
#         page_obj = paginator.get_page(page_number)

#         # Build logs for template
#         for entry in page_obj:
#             for column, change in (entry.changes_dict or {}).items():
#                 logs.append({
#                     "EntityName": entry.content_type.model,
#                     "RowID": entry.object_id,
#                     "ColumnName": column,
#                     "OldValue": change[0],
#                     "NewValue": change[1],
#                     "Action": entry.get_action_display(),
#                     "User": entry.actor.username if entry.actor else None,
#                     "Timestamp": entry.timestamp,
#                 })

#         return {
#             "page_obj": page_obj,
#             "object_list": logs,
#         }


class BOMAuditLogCRUDView(BaseCRUDView):
    model = LogEntry
    form_class = None

    def get_extra_context(self):
        logs = []

        # Get allowed entities dynamically from URL
        allowed_entities = self.request.GET.getlist("entity")

        entries = (
            LogEntry.objects
            .select_related("actor", "content_type")
        )

        # Apply filter only if entities provided
        if allowed_entities:
            entries = entries.filter(content_type__model__in=allowed_entities)
        
        entries = entries.order_by("-timestamp")
        total_records = entries.count()
        page_number = self.request.GET.get("page", 1)
        paginator = Paginator(entries, 10)
        page_obj = paginator.get_page(page_number)
        
        for entry in page_obj:
            for column, change in (entry.changes_dict or {}).items():
                logs.append({
                    "EntityName": entry.content_type.model,
                    "RowID": entry.object_id,
                    "ColumnName": column,
                    "OldValue": resolve_fk(entry, column, change[0]),
                    "NewValue": resolve_fk(entry, column, change[1]),
                    "Action": entry.get_action_display(),
                    "User": entry.actor.username if entry.actor else None,
                    "Timestamp": entry.timestamp,
                    "RecordsTotal": total_records,  
                })
        
        return {
            "page_obj": page_obj,
            "object_list": logs,
            "RecordsTotal": total_records,
            "total_pages": paginator.num_pages,
        }

# from rest_framework.response import Response
# from rest_framework.decorators import api_view
# @api_view(['GET'])
# def audit_list(request):
#     logs = []

#         # Get allowed entities dynamically from URL
#         allowed_entities = self.request.GET.getlist("entity")

#         entries = (
#             LogEntry.objects
#             .select_related("actor", "content_type")
#         )

#         # Apply filter only if entities provided
#         if allowed_entities:
#             entries = entries.filter(content_type__model__in=allowed_entities)
#         #import pdb; pdb.set_trace();

#         entries = entries.order_by("-timestamp")
#         total_records = entries.count()
#         page_number = self.request.GET.get("page", 1)
#         paginator = Paginator(entries, 10)
#         page_obj = paginator.get_page(page_number)

#         for entry in page_obj:
#             for column, change in (entry.changes_dict or {}).items():
#                 logs.append({
#                     "EntityName": entry.content_type.model,
#                     "RowID": entry.object_id,
#                     "ColumnName": column,
#                     "OldValue": resolve_fk(entry, column, change[0]),
#                     "NewValue": resolve_fk(entry, column, change[1]),
#                     "Action": entry.get_action_display(),
#                     "User": entry.actor.username if entry.actor else None,
#                     "Timestamp": entry.timestamp,
#                     #"RecordsTotal": total_records,  
#                 })
        
#         return {
#             "page_obj": page_obj,
#             "object_list": logs,
#         }
    # allowed_entities = request.GET.getlist("entity")
    # entries = (
    #     LogEntry.objects
    #     .select_related("actor", "content_type")
    # )

    # # Apply filter only if entities provided
    # if allowed_entities:
    #     entries = entries.filter(content_type__model__in=allowed_entities)
    
    # data = []
    # for entry in entries:
    #     data.append({
    #                 "EntityName": entry.content_type.model,
    #                 "RowID": entry.object_id,
    #                 "Action": entry.get_action_display(),
    #                 "User": entry.actor.username if entry.actor else None,
    #                 "Timestamp": entry.timestamp,
    #                 #"RecordsTotal": total_records,  
    #                 })
    # return Response({"data": data})