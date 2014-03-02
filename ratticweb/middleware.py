from django.utils.cache import patch_cache_control
from django.conf import settings


class DisableClientSideCachingMiddleware(object):
    """
    We don't want to cache any page that we dynamically. Additionally
    we want to force no_store to be true so that browsers cannot save
    passwords or other data to disk. This makes most browsers refresh
    the page when the back button is used.
    """
    def process_response(self, request, response):
        patch_cache_control(response,
            no_cache=True,
            no_store=True,
            must_revalidate=True,
            )
        return response


class XUACompatibleMiddleware(object):
    """
    Add a X-UA-Compatible header to the response
    This header tells to Internet Explorer to render page with latest
    possible version or to use chrome frame if it is installed.
    """
    def process_response(self, request, response):
        response['X-UA-Compatible'] = 'IE=edge,chrome=1'
        return response


class CSPMiddleware(object):
    """
    Adds a Content-Security-Policy header to the response. This header
    makes browsers refuse to load content from domains that are not Rattic.
    """
    def process_response(self, request, response):
        policy = 'default-src %s' % ' '.join(settings.ALLOWED_HOSTS)
        response['Content-Security-Policy'] = policy
        return response
