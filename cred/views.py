from django.shortcuts import render, get_object_or_404
from models import Cred
from django.http import Http404

def list(request):
    cred = Cred.objects.filter(group__in=request.user.groups.all())
    return render(request, 'cred_list.html', {'credlist': cred})

def detail(request, cred_id):
    cred = get_object_or_404(Cred, pk=cred_id)
    if cred.group not in request.user.groups.all():
        raise Http404
    return render(request, 'cred_detail.html', {'cred' : cred})
