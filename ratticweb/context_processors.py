from cred.models import CredChangeQ
from django.conf import settings
from django.utils import timezone


def base_template_reqs(request):
    cntx = {
        'pageurl': request.path,
        'LDAP_ENABLED': settings.LDAP_ENABLED,
        'GOAUTH2_ENABLED': settings.GOAUTH2_ENABLED,
        'EXPORT_ENABLED': not settings.RATTIC_DISABLE_EXPORT,
        'TEMPLATE_DEBUG': settings.TEMPLATE_DEBUG,
        'ALLOWPWCHANGE': not (settings.LDAP_ENABLED
            and not settings.AUTH_LDAP_ALLOW_PASSWORD_CHANGE),
        'rattic_icon': 'rattic/img/rattic_icon_normal.png',
        'rattic_logo': 'rattic/img/rattic_logo_normal.svg',
    }

    if settings.HELP_SYSTEM_FILES:
        cntx['helplinks'] = True
    else:
        cntx['helplinks'] = False

    if request.user.is_authenticated():
        cntx['changeqcount'] = CredChangeQ.objects.for_user(request.user).count()

    return cntx


def logo_selector(request):
    cntx = {}

    tz = timezone.get_current_timezone()
    time = tz.normalize(timezone.now())

    if ((time.hour > 20 and time.hour < 24) or
       (time.hour >= 0 and time.hour < 6)):
        cntx['rattic_icon'] = 'rattic/img/rattic_icon_sleeping.png'
        cntx['rattic_logo'] = 'rattic/img/rattic_logo_sleeping.svg'

    return cntx
