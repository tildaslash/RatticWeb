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
def cred_icon(iconname, field=None):
    data = get_icon_data()[iconname]

    alt = 'alt="%s"' % iconname
    stylesize = 'height: %spx; width: %spx; ' % (data['height'], data['width'])
    bgurl = settings.STATIC_URL + settings.CRED_ICON_SPRITE
    stylebg = 'background: url(%s) -%spx -%spx; ' % (bgurl, data['xoffset'], data['yoffset'])
    style = 'style="' + stylesize + stylebg + '"'
    src = 'src="' + settings.STATIC_URL + settings.CRED_ICON_CLEAR + '"'

    onclick = ''

    if field is not None:
        onclick = 'onclick="$(\'input#id_%s\').val(\'%s\');$(\'#logoModal\').modal(\'hide\')"' % (field, iconname)

    return '<img %s %s %s %s>' % (alt, style, src, onclick)
