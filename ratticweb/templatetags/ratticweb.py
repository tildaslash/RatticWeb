from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def url_root():
    return settings.RATTIC_ROOT_URL

