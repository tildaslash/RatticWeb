from django.utils.cache import patch_cache_control


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
        policy = "default-src 'self';style-src 'self' 'unsafe-inline'"
        response['Content-Security-Policy'] = policy
        return response


class HSTSMiddleware(object):
    """
    If a requests arrives via a secured channel, this tells the browser to
    only use secure connections to request further pages. This makes it much
    harder to strip SSL from the site.

    See: http://en.wikipedia.org/wiki/HTTP_Strict_Transport_Security
    """
    def process_response(self, request, response):
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000'
        return response


class DisableContentTypeSniffing(object):
    """
    This Middleware adds a custom header to disable IE8's Content-Type
    sniffing. The Sniffing in IE8 can cause certain files to be interpreted
    with a different Content-Type than the server indicated. This can cause
    security issues and since RatticDB always sends the intended Content-Type
    it can be disabled.
    """
    def process_response(self, request, response):
        response['X-Content-Type-Options'] = 'nosniff'
        return response
