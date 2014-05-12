from django import template
from django.conf import settings

from cred.icon import get_icon_data

register = template.Library()


@register.simple_tag
def cred_icon(iconname, txtfield=None, imgfield=None, tagid=None):
    """
    Generates the HTML used to display an icon. If the icon cannot be found
    it reverts to the default icon mentioned in settings CRED_ICON_DEFAULT.
    It is used on the details pages and as part of the CredIconChooser widget.
    """

    # Get info for the icon, if that wont work, get info for the default icon
    try:
        data = get_icon_data()[iconname]
    except KeyError:
        data = get_icon_data()[settings.CRED_ICON_DEFAULT]

    # Get the URL for the blank image (goes in the href)
    blankimg = settings.STATIC_URL + settings.CRED_ICON_CLEAR

    # What CSS classes does our icon need
    classes = ['rattic-icon', data['css-class']]

    # If the icon is clickable append the clickable class
    if txtfield is not None or imgfield is not None:
        classes.append('rattic-icon-clickable')

    # Build the HTML
    tag = '<img '
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
