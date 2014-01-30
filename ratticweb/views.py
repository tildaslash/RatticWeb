from django.shortcuts import redirect
from django.core.urlresolvers import reverse


def home(request):
    if request.user.is_authenticated():
        return redirect(reverse('cred.views.list'))
    else:
        return redirect(reverse('login'))
