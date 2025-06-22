from django import template

register = template.Library()

@register.filter(name="get_item")
def get_item(dictionary, key):
    """
    Safely fetches a value from a dictionary using the provided key.
    Usage: {{ my_dict|get_item:"some_key" }}
    """
    return dictionary.get(key)

@register.filter(name="get_dynamic")
def get_dynamic(obj, attr):
    """
    Dynamically accesses an attribute from any object or model instance.
    Usage: {{ object|get_dynamic:"field_name" }}
    """
    return getattr(obj, attr, None)

@register.filter(name="train_id")
def train_id(train):
    """
    Returns train.pk if it's an integer; otherwise falls back to train.number.
    This ensures reverse URL lookups never fail.
    Usage: {% url 'book:book' train|train_id date %}
    """
    pk = getattr(train, "pk", None)
    try:
        return int(pk)
    except (ValueError, TypeError):
        return getattr(train, "number", pk)