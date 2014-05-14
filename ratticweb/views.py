from django.shortcuts import redirect, render
from django.core.urlresolvers import reverse


def home(request):
    if request.user.is_authenticated():
        return redirect(reverse('cred.views.list'))
    else:
        nextpage = request.GET.get('next', '')
        return render(request, 'home.html', {'next': nextpage})


def handle500(request):
    return render(request, '500.html', status=500)


def handle404(request):
    return render(request, '404.html', status=404)
