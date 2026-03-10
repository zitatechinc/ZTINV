# templatetags/product_extras.py
from django import template

register = template.Library()

@register.filter
def get_field(obj, field_name):
    value = getattr(obj, field_name, 'NA')
    return value
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

