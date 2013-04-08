from django.conf import settings
from django.http import Http404


def not_with_ldap(fn):
    if settings.LDAP_ENABLED:
        def _dont(*args, **kwargs):
            raise Http404
        return _dont
    else:
        return fn


def only_with_ldap(fn):
    if not settings.LDAP_ENABLED:
        def _dont(*args, **kwargs):
            raise Http404
        return _dont
    else:
        return fn
