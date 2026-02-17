# templatetags/product_extras.py
from django import template
import json 

register = template.Library()

@register.filter
def get_field(obj, field_name):
    value = getattr(obj, field_name, 'NA')
    return 

@register.filter
def pretty_json(value):
    try:
        return json.dumps(json.loads(value), indent=4, ensure_ascii=False)
    except Exception as e:
        print (e)
        return value

@register.filter
def payload_pretty_json(value):
    try:
        value = json.loads(value)
        attributes = json.loads(value['attributes'])
        value['attributes'] = attributes
        return json.dumps(value, indent=4, ensure_ascii=False)
    except Exception as e:
        print (e)
        return value
