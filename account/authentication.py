import logging

from tastypie.authentication import ApiKeyAuthentication
from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from django.conf import settings

import ldap
from account.models import ApiKey


logger = logging.getLogger()


class MultiApiKeyAuthentication(ApiKeyAuthentication):
    def get_key(self, user, api_key):
        try:
            ApiKey.objects.get(user=user, key=api_key)
        except ApiKey.DoesNotExist:
            return self._unauthorized()

        return True


class ADUser(object):
    """
    https://djangosnippets.org/snippets/1397/
    """
    ldap_connection = None
    AD_SEARCH_FIELDS = ['mail', 'givenName', 'sn', 'sAMAccountName']

    @classmethod
    def get_ldap_url(cls):
        return settings.AUTH_LDAP_SERVER_URI

    def __init__(self, username):
        self.username = username
        self.user_bind_name = "%s@%s" % (self.username, settings.AUTH_LDAP_DOMAIN)
        self.is_bound = False
        self.has_data = False

        self.first_name = None
        self.last_name = None
        self.email = None

    def connect(self, password):
        had_connection = ADUser.ldap_connection is not None
        ret = self._connect(password)
        # WORKAROUND: for invalid connection
        if not ret and had_connection and ADUser.ldap_connection is None:
            logger.warning("AD reset connection - invalid connection, try again with new connection")
            ret = self._connect(password)
        return ret

    def _connect(self, password):
        if not password:
            return False  # Disallowing null or blank string as password
        try:
            if ADUser.ldap_connection is None:
                logger.info("AD auth backend ldap connecting")
                ADUser.ldap_connection = ldap.initialize(self.get_ldap_url())
                assert self.ldap_connection == ADUser.ldap_connection  # python won't do that ;)
            self.ldap_connection.simple_bind_s(self.user_bind_name, password)
            self.is_bound = True
        except Exception, e:
            if str(e).find("connection invalid") >= 0:
                logger.warning("AD reset connection - it looks like invalid: %s" % (str(e)))
                ADUser.ldap_connection = None
            else:
                logger.error("AD auth backend ldap - probably bad credentials: %s" % (str(e)))
            return False
        return True

    def disconnect(self):
        if self.is_bound:
            logger.info("AD auth backend ldap unbind")
            self.ldap_connection.unbind_s()
            self.is_bound = False

    def get_data(self):
        try:
            assert self.ldap_connection
            # NOTE: Something goes wrong in my case - ignoring this until solved :(
            res = self.ldap_connection.search_ext_s(settings.AUTH_LDAP_DOMAIN,
                                                    ldap.SCOPE_SUBTREE,
                                                    "sAMAccountName=%s" % self.username,
                                                    self.AD_SEARCH_FIELDS)
            self.disconnect()
            if not res:
                logger.error("AD auth ldap backend error by searching %s. No result." % settings.AUTH_LDAP_USER_SEARCH)
                return False
            assert len(res) >= 1, "Result should contain at least one element: %s" % res
            result = res[0][1]
        except Exception, e:
            self.disconnect()
            logger.error("AD auth backend error by fetching ldap data: %s" % (str(e)))
            return False

        try:
            self.first_name = None
            if 'givenName' in result:
                self.first_name = result['givenName'][0]

            self.last_name = None
            if 'sn' in result:
                self.last_name = result['sn'][0]

            self.email = None
            if 'mail' in result:
                self.email = result['mail'][0]
            self.has_data = True
        except Exception, e:
            logger.error("AD auth backend error by reading fetched data: %s" % (str(e)))
            return False

        return True

    def __del__(self):
        try:
            self.disconnect()
        except Exception, e:
            logger.error("AD auth backend error when disconnecting: %s" % (str(e)))
            return False

    def __str__(self):
        return "AdUser(<%s>, connected=%s, is_bound=%s, has_data=%s)" % (
            self.username, self.ldap_connection is not None, self.is_bound, self.has_data)


class ActiveDirectoryBackend(ModelBackend):
    def authenticate(self, username=None, password=None):
        logger.info("AD auth backend for %s" % username)
        aduser = ADUser(username)

        if not aduser.connect(password):
            return None

        user = None
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User(username=username, is_staff=False, is_superuser=False)

        if not aduser.get_data():
            logger.warning(
                "AD auth backend failed when reading data for %s. User detail data won't be updated in User model." % username)
        else:
            # NOTE: update user data exchange to User model
            assert user.username == aduser.username
            user.first_name = aduser.first_name
            user.last_name = aduser.last_name
            user.email = aduser.email
            logger.warning("AD auth backend overwriting auth.User data with data from ldap for %s." % username)
        user.save()
        logger.info("AD auth backend check passed for %s" % username)
        return user