from django import template

from cred.icon import allicons

register = template.Library()

# Sprite Tag
# <img alt="Guitar" style="height: 10px; width: 10px; background:
# url(/static/rattic/img/sprite.png) -1078px -0px;"
# src="/static/rattic/img/clear.gif">

# Non-sprite Tag
# <img src="/static/rattic/img/credicon/Key.png">


@register.simple_tag
def cred_icon(iconname, field=None):
    if iconname not in allicons:
        return ''

    onclick = ''

    if field is not None:
        onclick = 'onclick="$(\'input#id_%s\').val(\'%s\');$(\'#logoModal\').modal(\'hide\')"' % (field, iconname)

    return '<img src="/static/rattic/img/credicons/%s" %s />' % (iconname, onclick)
