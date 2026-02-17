from django import template

# Create a new template library to register custom filters
register = template.Library()

@register.filter
def get_item(collection, key):
    """
    Custom template filter to retrieve an item from a dictionary or a list using a key or index.

    Usage in templates:
        {{ my_dict|get_item:"key" }}
        {{ my_list|get_item:"0" }}
    """
    if isinstance(collection, dict):
        # Safely get the value from a dictionary using the key
        return collection.get(key)
    
    elif isinstance(collection, list):
        try:
            # Attempt to convert key to integer and get item from list
            return collection[int(key)]  
        except (ValueError, IndexError):
            # Return None if key is not an integer or index is out of range
            return None  
    
    # If collection is neither dict nor list, return None
    return None  

@register.filter
def indian_notation(value):
    """
    Custom template filter to format numbers using Indian currency notation:
        Cr (Crore), L (Lakh), K (Thousand)

    Usage in templates:
        {{ amount|indian_notation }}
    """
    try:
        # Try to convert the input to a float
        value = float(value)
    except (ValueError, TypeError):
        # Return the original value if conversion fails
        return value

    # Format the number according to Indian units
    if value >= 10_000_000:
        return f"{value / 10_000_000:.2f} Cr"
    elif value >= 100_000:
        return f"{value / 100_000:.2f} L"
    elif value >= 1_000:
        return f"{value / 1_000:.2f} K"
    else:
        return f"{value:.0f}"  # Return without decimal if less than 1000

