from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from models import Cred, CredForm, CredAudit, TagForm, Tag, CredChangeQ
from django.http import Http404
from django.contrib.auth.decorators import login_required

@login_required
def list(request):
    cred = Cred.objects.for_user(request.user)
    return render(request, 'cred_list.html', {'credlist': cred})

@login_required
def list_by_tag(request, tag_id):
    tag = get_object_or_404(Tag, pk=tag_id)
    cred = Cred.objects.for_user(request.user).filter(tags=tag)
    return render(request, 'cred_list.html', {'credlist': cred, 'tag': tag})

@login_required
def list_by_search(request, search):
    cred = Cred.objects.for_user(request.user).filter(title__contains=search)
    tag = Tag.objects.filter(name__contains=search)
    return render(request, 'cred_list.html', {'credlist': cred, 'tag':tag, 'showtaglist':True})

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
        form = CredForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            CredAudit(audittype=CredAudit.CREDADD, cred=form.instance, user=request.user).save()
            return HttpResponseRedirect('/cred/list')
    else:
        form = CredForm(request.user)

    return render(request, 'cred_edit.html', {'form': form, 'action':
        '/cred/add/'})

@login_required
def edit(request, cred_id):
    cred = get_object_or_404(Cred, pk=cred_id)
    # Check user has perms
    if cred.group not in request.user.groups.all():
        raise Http404
    if request.method == 'POST':
        form = CredForm(request.user, request.POST, instance=cred)
        if form.is_valid():
            # Assume metedata change
            chgtype = CredAudit.CREDMETACHANGE
            # Unless something thats not metadata changes
            for c in form.changed_data:
                if c not in Cred.METADATA:
                    chgtype = CredAudit.CREDCHANGE
            # Clear pre-existing change queue items
            if chgtype == CredAudit.CREDCHANGE:
                CredChangeQ.objects.filter(cred=cred).delete()
            # Create audit log
            CredAudit(audittype=chgtype, cred=cred, user=request.user).save()
            form.save()
            return HttpResponseRedirect('/cred/list')
    else:
        form = CredForm(request.user, instance=cred)
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
    return render(request, 'cred_detail.html',{'cred' : cred, 'action':'/cred/delete/' + cred_id + '/', 'delete':True})


# Categories 
@login_required
def tagadd(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/cred/list')
    else:
        form = TagForm()

    return render(request, 'cred_tagedit.html', {'form': form,})

@login_required
def tagedit(request, tag_id):
    tag = get_object_or_404(Tag, pk=tag_id)
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/cred/list')
    else:
        form = TagForm(instance=tag)

    return render(request, 'cred_tagedit.html', {'form': form,})

@login_required
def tagdelete(request, tag_id):
    tag = get_object_or_404(Tag, pk=tag_id)
    if request.method == 'POST':
        tag.delete()
        return HttpResponseRedirect('/cred/list')
    return render(request, 'cred_tagdelete.html',{})

@login_required
def viewqueue(request):
    queue = CredChangeQ.objects.for_user(request.user)
    return render(request, 'cred_queue.html', {'queue': queue})

@login_required
def addtoqueue(request, cred_id):
    cred = get_object_or_404(Cred, pk=cred_id)
    # Check user has perms
    if cred.group not in request.user.groups.all():
        raise Http404
    CredChangeQ.objects.add_to_changeq(cred)
    return HttpResponseRedirect('/cred/viewqueue')

