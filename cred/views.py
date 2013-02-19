from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from models import Cred, CredForm, CredAudit
from django.http import Http404
from django.contrib.auth.decorators import login_required

@login_required
def list(request):
    cred = Cred.objects.filter(group__in=request.user.groups.all())
    return render(request, 'cred_list.html', {'credlist': cred})

@login_required
def detail(request, cred_id):
    cred = get_object_or_404(Cred, pk=cred_id)
    CredAudit(audittype=CredAudit.CREDVIEW, cred=cred, user=request.user).save()
    # Check user has perms
    if cred.group not in request.user.groups.all():
        raise Http404
    return render(request, 'cred_detail.html', {'cred' : cred, 'showaudit': request.user.is_staff})

@login_required
def add(request):
    if request.method == 'POST':
        form = CredForm(request.POST)
        if form.is_valid():
            form.save()
            CredAudit(audittype=CredAudit.CREDADD, cred=form.instance, user=request.user).save()
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
            # Assume metedata change
            chgtype = CredAudit.CREDMETACHANGE
            # Unless something thats not metadata changes
            for c in form.changed_data:
                if c not in Cred.METADATA:
                    chgtype = CredAudit.CREDCHANGE
            # Create audit log
            CredAudit(audittype=chgtype, cred=cred, user=request.user).save()
            form.save()
            return HttpResponseRedirect('/cred/list')
    else:
        form = CredForm(instance=cred)
    	CredAudit(audittype=CredAudit.CREDVIEW, cred=cred, user=request.user).save()

    return render(request, 'cred_edit.html', {'form': form, 'action':
        '/cred/edit/' + cred_id + '/'})

@login_required
def delete(request, cred_id):
    cred = get_object_or_404(Cred, pk=cred_id)
    # Check user has perms
    if cred.group not in request.user.groups.all():
        raise Http404
    if request.method == 'POST':
        cred.delete()
        return HttpResponseRedirect('/cred/list')
    return render(request, 'cred_delete.html',{'action':'/cred/delete/' + cred_id + '/'})
