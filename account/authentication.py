from tastypie.authentication import ApiKeyAuthentication
from account.models import ApiKey


class MultiApiKeyAuthentication(ApiKeyAuthentication):
    def get_key(self, user, api_key):
        try:
            ApiKey.objects.get(user=user, key=api_key)
        except ApiKey.DoesNotExist:
            return self._unauthorized()

        return True
