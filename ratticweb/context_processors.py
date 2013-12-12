from cred.models import CredChangeQ
from django.conf import settings


def base_template_reqs(request):
    cntx = {
        'pageurl': request.path,
        'LDAP_ENABLED': settings.LDAP_ENABLED,
        'TEMPLATE_DEBUG': settings.TEMPLATE_DEBUG,
        'ALLOWPWCHANGE': not (settings.LDAP_ENABLED
            and not settings.AUTH_LDAP_ALLOW_PASSWORD_CHANGE),
    }

    if settings.HELP_SYSTEM_FILES:
        cntx['helplinks'] = True
    else:
        cntx['helplinks'] = False

    if request.user.is_authenticated():
        cntx['changeqcount'] = CredChangeQ.objects.for_user(request.user).count()

    return cntx
