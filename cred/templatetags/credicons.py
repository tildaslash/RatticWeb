from django import template
from django.conf import settings

from cred.icon import get_icon_data

register = template.Library()

# Sprite Tag
# <img alt="Guitar" style="height: 10px; width: 10px; background:
# url(/static/rattic/img/sprite.png) -1078px -0px;"
# src="/static/rattic/img/clear.gif">

# Non-sprite Tag
# <img src="/static/rattic/img/credicon/Key.png">


@register.simple_tag
def cred_icon(iconname, txtfield=None, imgfield=None, tagid=None):
    try:
        data = get_icon_data()[iconname]
    except KeyError:
        data = get_icon_data()[settings.CRED_ICON_DEFAULT]

    blankimg = settings.STATIC_URL + settings.CRED_ICON_CLEAR
    classes = ['rattic-icon', data['css-class']]

    if txtfield is not None or imgfield is not None:
        classes.append('rattic-icon-clickable')

    tag =  '<img '
    tag += 'src="%s" ' % blankimg
    tag += 'data-icon-name="%s" ' % data['filename']
    if tagid is not None:
        tag += 'id="%s" ' % tagid
    if txtfield is not None:
        tag += 'data-txt-field="%s" ' % txtfield
    if imgfield is not None:
        tag += 'data-img-field="%s" ' % imgfield
    if 'rattic-icon-clickable' in classes:
        tag += 'data-dismiss="modal" '
    tag += 'class="%s" ' % ' '.join(classes)
    tag += '>'

    return tag

