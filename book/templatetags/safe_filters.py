from django import template
register = template.Library()

@register.filter
def train_id_for_url(train):
    return train.pk if isinstance(train.pk, int) else train.number