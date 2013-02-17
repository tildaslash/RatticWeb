from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from models import Cred, CredForm
from django.http import Http404
from django.contrib.auth.decorators import login_required

@login_required
def list(request):
    cred = Cred.objects.filter(group__in=request.user.groups.all())
    return render(request, 'cred_list.html', {'credlist': cred})

@login_required
def detail(request, cred_id):
    cred = get_object_or_404(Cred, pk=cred_id)
    # Check user has perms
    if cred.group not in request.user.groups.all():
        raise Http404
    return render(request, 'cred_detail.html', {'cred' : cred})

@login_required
def add(request):
    if request.method == 'POST':
        form = CredForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/cred/list')
    else:
        form = CredForm()

    return render(request, 'cred_edit.html', {'form': form, 'action':
        '/cred/add/'})

@login_required
def edit(request, cred_id):
    cred = get_object_or_404(Cred, pk=cred_id)
    # Check user has perms
    if cred.group not in request.user.groups.all():
        raise Http404
    if request.method == 'POST':
        form = CredForm(request.POST, instance=cred)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/cred/list')
    else:
        form = CredForm(instance=cred)

    return render(request, 'cred_edit.html', {'form': form, 'action':
        '/cred/edit/' + cred_id + '/'})

