from django import template

register = template.Library()

@register.filter
def bom_balance(component, bom_item):
    return component.get_bom_item_balance_qty(bom_item)
@register.filter
def issued_raw_qty(component, bom_item):
    return component.get_bom_item_issued_qty(bom_item)

@register.filter
def multiply(a, b):
    return (a or 0) * (b or 0)
