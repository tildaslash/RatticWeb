from django.utils.cache import patch_cache_control

class DisableClientSideCachingMiddleware(object):
    def process_response(self, request, response):
        patch_cache_control(response,
            no_cache=True,
            no_store=True,
            must_revalidate=True,
            )
        return response
