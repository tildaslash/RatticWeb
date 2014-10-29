from django.contrib.auth import logout
from django.conf import settings
from django.utils.timezone import now
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect


class StrictAuthentication:
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Logout users who have been disabled
        if request.user.is_authenticated() and not request.user.is_active:
            logout(request)


class PasswordExpirer:
    def process_view(self, request, view_func, view_args, view_kwargs):
        # If there is no password expiry, or LDAP is enabled do nothing
        if not settings.PASSWORD_EXPIRY or settings.LDAP_ENABLED:
            return

        # If no user is logged in do nothing
        if not request.user.is_authenticated():
            return

        # If they aren't currently trying to change their password
        changepassurl = reverse('password_change')
        if request.method != 'GET' or request.path == changepassurl:
            return

        # Figure out when they next need to change password
        nextpwchange = request.user.profile.password_changed + settings.PASSWORD_EXPIRY

        # If that is in the past then force them to change it
        if nextpwchange < now():
            return HttpResponseRedirect(changepassurl)
