from django.contrib.auth import logout
from django.conf import settings
from django.utils.timezone import now
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

class StrictAuthentication:
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated() and not request.user.is_active:
            logout(request)

class PasswordExpirer:
    def process_view(self, request, view_func, view_args, view_kwargs):
        if not settings.PASSWORD_EXPIRY:
            return

        changepassurl = reverse('django.contrib.auth.views.password_change')
        if request.method != 'GET' or request.path == changepassurl:
            return

        nextpwchange = request.user.profile.password_changed + settings.PASSWORD_EXPIRY
        if nextpwchange < now():
            return HttpResponseRedirect(changepassurl)

