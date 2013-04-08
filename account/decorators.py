from django.conf import settings
from django.http import Http404


def not_with_ldap(fn):
    if settings.LDAP_ENABLED:
        def dont():
            raise Http404
        return dont
    else:
        return fn


def only_with_ldap(fn):
    if not settings.LDAP_ENABLED:
        def dont():
            raise Http404
        return dont
    else:
        return fn
