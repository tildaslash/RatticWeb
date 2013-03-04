from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from models import Cred, CredForm, CredAudit, TagForm, Tag, CredChangeQ
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@login_required
def list(request):
    cred_list = Cred.objects.for_user(request.user)
    paginator = Paginator(cred_list, request.user.profile.items_per_page)
    page = request.GET.get('page')
    try:
        cred = paginator.page(page)
    except PageNotAnInteger:
        cred = paginator.page(1)
    except EmptyPage:
        cred = paginator.page(paginator.num_pages)
    return render(request, 'cred_list.html', {'credlist': cred})

@login_required
def list_by_tag(request, tag_id):
    tag = get_object_or_404(Tag, pk=tag_id)
    cred_list = Cred.objects.for_user(request.user).filter(tags=tag)
    paginator = Paginator(cred_list, request.user.profile.items_per_page)
    page = request.GET.get('page')
    try:
        cred = paginator.page(page)
    except PageNotAnInteger:
        cred = paginator.page(1)
    except EmptyPage:
        cred = paginator.page(paginator.num_pages)
    title = 'Passwords for tag: ' + tag.name
    return render(request, 'cred_list.html', {'credlist': cred, 'tag': tag, 'credtitle': title})

@login_required
def tags(request):
    tags = Tag.objects.all()
    return render(request, 'cred_tags.html', {'tags': tags})

@login_required
def list_by_search(request, search):
    cred_list = Cred.objects.for_user(request.user).filter(title__contains=search)
    tag = Tag.objects.filter(name__contains=search)
    paginator = Paginator(cred_list, request.user.profile.items_per_page)
    page = request.GET.get('page')
    try:
        cred = paginator.page(page)
    except PageNotAnInteger:
        cred = paginator.page(1)
    except EmptyPage:
        cred = paginator.page(paginator.num_pages)
    title = 'Passwords for search: ' + search
    return render(request, 'cred_list.html', {'credlist': cred, 'tag':tag, 'showtaglist':True, 'credtitle': title})

@login_required
def detail(request, cred_id):
    cred = get_object_or_404(Cred, pk=cred_id)

    CredAudit(audittype=CredAudit.CREDVIEW, cred=cred, user=request.user).save()

    # Check user has perms
    if cred.group not in request.user.groups.all():
        raise Http404

    lastchange = CredAudit.objects.filter(
            cred=cred,
            audittype__in=[CredAudit.CREDCHANGE, CredAudit.CREDADD],
            ).latest()

    if request.user.is_staff:
        credlogs = cred.logs.all()[:5]
        morelink = reverse('staff.views.audit_by_cred', args=(cred.id,))
    else:
        credlogs = None
        morelink = None

    return render(request, 'cred_detail.html', {
        'cred' : cred,
        'credlogs': credlogs,
        'lastchange': lastchange,
        'morelink': morelink
        })

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
    return HttpResponseRedirect('/cred/viewqueue/')

@login_required
def bulkaddtoqueue(request):
    tochange = Cred.objects.filter(id__in=request.POST.getlist('tochange'))
    usergroups = request.user.groups.all()
    for c in tochange:
        # Staff have access to add bulk, so change advice can be used
        if request.user.is_staff or (cred.group not in usergroups):
            CredChangeQ.objects.add_to_changeq(c)

    return HttpResponseRedirect('/cred/viewqueue/')

