# audit/utils.py
from django.apps import apps
from django.db.models import Model

def resolve_fk(entry, field_name, value):
    model = entry.content_type.model_class()

    # Field not found → return as-is
    try:
        field = model._meta.get_field(field_name)
    except:
        return value

    # Not a FK → return value
    if not field.is_relation or not field.many_to_one:
        return value

    # FK → convert id → readable text
    related_model = field.related_model
    try:
        instance = related_model.objects.get(pk=value)
        return str(instance)
    except:
        return value
