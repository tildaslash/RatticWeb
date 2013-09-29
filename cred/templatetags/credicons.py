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
def cred_icon(iconname, callback=None, tagid=None, tagname=None, tagnumber=None):
    cred_icon.count += 1

    try:
        data = get_icon_data()[iconname]
    except KeyError:
        return ''

    alt = 'alt="%s"' % iconname
    stylesize = 'height: %spx; width: %spx; ' % (data['height'], data['width'])
    bgurl = settings.STATIC_URL + settings.CRED_ICON_SPRITE
    stylebg = 'background: url(%s) -%spx -%spx; ' % (bgurl, data['xoffset'], data['yoffset'])
    style = 'style="' + stylesize + stylebg + '"'
    src = 'src="' + settings.STATIC_URL + settings.CRED_ICON_CLEAR + '"'

    if tagid is None and tagname is not None and tagnumber is not None:
      tagid = tagname + '_' + str(tagnumber)
    elif tagid is None and (tagname is None or tagnumber is None):
      tagid = 'credicon_' + str(cred_icon.count)

    if callback is None:
      onclick=''
    else:
      onclick='onclick="' + callback + '(\'' + iconname + '\', \'' + tagid + '\')"'

    return '<img id="%s" %s %s %s %s>' % (tagid, alt, style, src, onclick)

cred_icon.count = 0
