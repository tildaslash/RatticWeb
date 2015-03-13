from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import ugettext as _

from models import Cred, CredAudit, Tag, CredChangeQ
from search import cred_search
from forms import ExportForm, CredForm, TagForm
from exporters import export_keepass
from cred.icon import get_icon_list

from django.contrib.auth.models import Group


@login_required
def download(request, cfilter="special", value="all"):
    if request.method == 'POST':  # If the form has been submitted...

        form = ExportForm(request.POST)  # A form bound to the POST data
        if form.is_valid():  # All validation rules pass

            # Get the creds to export
            (search_object, creds) = cred_search(request.user, cfilter, value)
            filename = 'RatticExport.kdb'

            # Decide on the filename
            if cfilter == 'tag':
                filename = 'RatticExportTag-%s.kdb' % search_object.name

            elif cfilter == 'group':
                filename = 'RatticExportGroup-%s.kdb' % search_object.name

            elif cfilter == 'search':
                filename = 'RatticExportSearch-%s.kdb' % search_object

            elif cfilter == 'special' and value == 'all':
                filename = 'RatticExportAll.kdb'

            elif cfilter == 'special' and value == 'trash':
                filename = 'RatticExportTrash.kdb'

            else:
                raise Http404

            # Make the Audit logs
            auditlogs = []
            for c in creds:
                auditlogs.append(CredAudit(
                    audittype=CredAudit.CREDEXPORT,
                    cred=c,
                    user=request.user,
                ))

            # Create all Audit logs at once
            CredAudit.objects.bulk_create(auditlogs)

            # Give the Keepass file to the user
            return export_keepass(creds, form.cleaned_data['password'], filename)
    else:
        form = ExportForm()  # An unbound form

    return render(request, 'cred_export.html', {
        'form': form,
    })


@login_required
def list(request, cfilter='special', value='all', sortdir='ascending', sort='title', page=1):
    # Setup basic stuff
    viewdict = {
        'credtitle': _('All passwords'),
        'alerts': [],
        'filter': unicode(cfilter).lower(),
        'value': unicode(value).lower(),
        'sort': unicode(sort).lower(),
        'sortdir': unicode(sortdir).lower(),
        'page': unicode(page).lower(),
        'groups': request.user.groups,

        # Default buttons
        'buttons': {
            'add': True,
            'delete': True,
            'changeq': True,
            'tagger': True,
            'export': False,
        }
    }

    # Get groups if required
    get_groups = request.GET.getlist('group')

    if len(get_groups) > 0:
        groups = Group.objects.filter(id__in=get_groups)
    else:
        groups = Group.objects.all()

    # Perform the search
    (search_object, cred_list) = cred_search(request.user, cfilter, value, sortdir, sort, groups)

    # Apply the filters
    if cfilter == 'tag':
        viewdict['credtitle'] = _('Passwords tagged with %(tagname)s') % {'tagname': search_object.name, }
        viewdict['buttons']['export'] = True

    elif cfilter == 'group':
        viewdict['credtitle'] = _('Passwords in group %(groupname)s') % {'groupname': search_object.name, }
        viewdict['buttons']['export'] = True

    elif cfilter == 'search':
        viewdict['credtitle'] = _('Passwords for search "%(searchstring)s"') % {'searchstring': search_object, }
        viewdict['buttons']['export'] = True

    elif cfilter == 'history':
        viewdict['credtitle'] = _('Versions of: "%(credtitle)s"') % {'credtitle': search_object.title, }
        viewdict['buttons']['add'] = False
        viewdict['buttons']['delete'] = False
        viewdict['buttons']['changeq'] = False
        viewdict['buttons']['tagger'] = False

    elif cfilter == 'changeadvice':
        alert = {}
        alert['message'] = _("That user is now disabled. Here is a list of passwords that they have viewed that have not since been changed. You probably want to add them all to the change queue.")
        alert['type'] = 'info'

        viewdict['credtitle'] = _('Changes required for "%(username)s"') % {'username': search_object.username}
        viewdict['buttons']['add'] = False
        viewdict['buttons']['delete'] = True
        viewdict['buttons']['changeq'] = True
        viewdict['buttons']['tagger'] = False
        viewdict['alerts'].append(alert)

    elif cfilter == 'special' and value == 'all':
        viewdict['buttons']['export'] = True

    elif cfilter == 'special' and value == 'trash':
        viewdict['credtitle'] = _('Passwords in the trash')
        viewdict['buttons']['add'] = False
        viewdict['buttons']['undelete'] = True
        viewdict['buttons']['changeq'] = False
        viewdict['buttons']['tagger'] = False
        viewdict['buttons']['export'] = True

    elif cfilter == 'special' and value == 'changeq':
        viewdict['credtitle'] = _('Passwords on the Change Queue')
        viewdict['buttons']['add'] = False
        viewdict['buttons']['delete'] = False
        viewdict['buttons']['changeq'] = False
        viewdict['buttons']['tagger'] = False

    else:
        raise Http404

    # Apply the sorting rules
    if sortdir == 'ascending':
        viewdict['revsortdir'] = 'descending'
    elif sortdir == 'descending':
        viewdict['revsortdir'] = 'ascending'
    else:
        raise Http404

    # Get the page
    paginator = Paginator(cred_list, request.user.profile.items_per_page)
    try:
        cred = paginator.page(page)
    except PageNotAnInteger:
        cred = paginator.page(1)
    except EmptyPage:
        cred = paginator.page(paginator.num_pages)

    # Get variables to give the template
    viewdict['credlist'] = cred

    # Create the form for exporting
    viewdict['exportform'] = ExportForm()

    return render(request, 'cred_list.html', viewdict)


@login_required
def tags(request):
    tags = {}
    for t in Tag.objects.all():
        tags[t] = t.visible_count(request.user)
    return render(request, 'cred_tags.html', {'tags': tags})


@login_required
def detail(request, cred_id):
    cred = get_object_or_404(Cred, pk=cred_id)

    # Check user has perms as owner or viewer
    if not cred.is_visible_by(request.user):
        raise Http404

    CredAudit(audittype=CredAudit.CREDVIEW, cred=cred, user=request.user).save()

    if request.user.is_staff:
        credlogs = cred.logs.all()[:5]
        morelink = reverse('staff.views.audit', args=('cred', cred.id))
    else:
        credlogs = None
        morelink = None

    # User is not in the password owner group, show a read-only UI
    if cred.group in request.user.groups.all():
        readonly = False
    else:
        readonly = True

    return render(request, 'cred_detail.html', {
        'cred': cred,
        'credlogs': credlogs,
        'morelink': morelink,
        'readonly': readonly,
        'groups': request.user.groups,
    })


@login_required
def downloadattachment(request, cred_id):
    # Get the credential
    cred = get_object_or_404(Cred, pk=cred_id)

    # Check user has perms
    if not cred.is_visible_by(request.user):
        raise Http404

    # Make sure there is an attachment
    if cred.attachment is None:
        raise Http404

    # Write the audit log, as a password view
    CredAudit(audittype=CredAudit.CREDPASSVIEW, cred=cred, user=request.user).save()

    # Send the result back in a way that prevents the browser from executing it,
    # forces a download, and names it the same as when it was uploaded.
    response = HttpResponse(mimetype='application/octet-stream')
    response.write(cred.attachment.read())
    response['Content-Disposition'] = 'attachment; filename="%s"' % cred.attachment_name
    response['Content-Length'] = response.tell()
    return response


@login_required
def add(request):
    if request.method == 'POST':
        form = CredForm(request.user, request.POST, request.FILES)
        if form.is_valid():
            form.save()
            CredAudit(audittype=CredAudit.CREDADD, cred=form.instance, user=request.user).save()
            return HttpResponseRedirect(reverse('cred.views.list'))
    else:
        form = CredForm(request.user)

    return render(request, 'cred_edit.html', {'form': form, 'action':
      reverse('cred.views.add'), 'icons': get_icon_list()})


@login_required
def edit(request, cred_id):
    cred = get_object_or_404(Cred, pk=cred_id)

    if cred.latest is not None:
        raise Http404

    next = request.GET.get('next', None)

    # Check user has perms
    if not cred.is_visible_by(request.user):
        raise Http404

    if request.method == 'POST':
        form = CredForm(request.user, request.POST, request.FILES, instance=cred)

        # Password change possible only for owner group
        if form.is_valid() and cred.group in request.user.groups.all():
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

            # If we dont have anywhere to go, go to the details page
            if next is None:
                return HttpResponseRedirect(reverse('cred.views.detail', args=(cred.id,)))
            else:
                return HttpResponseRedirect(next)
    else:
        form = CredForm(request.user, instance=cred)
        CredAudit(audittype=CredAudit.CREDPASSVIEW, cred=cred, user=request.user).save()

    return render(request, 'cred_edit.html', {'form': form,
        'action': reverse('cred.views.edit', args=(cred.id,)),
        'next': next,
        'icons': get_icon_list(),
        'cred': cred,
    })


@login_required
def delete(request, cred_id):
    cred = get_object_or_404(Cred, pk=cred_id)

    if cred.latest is not None:
        raise Http404

    try:
        lastchange = CredAudit.objects.filter(
            cred=cred,
            audittype__in=[CredAudit.CREDCHANGE, CredAudit.CREDADD],
        ).latest().time
    except CredAudit.DoesNotExist:
        lastchange = _("Unknown (Logs deleted)")

    # Check user has perms (user must be member of the password owner group)
    if not cred.is_owned_by(request.user):
        raise Http404
    if request.method == 'POST':
        CredAudit(audittype=CredAudit.CREDDELETE, cred=cred, user=request.user).save()
        cred.delete()
        return HttpResponseRedirect(reverse('cred.views.list'))

    CredAudit(audittype=CredAudit.CREDVIEW, cred=cred, user=request.user).save()

    return render(request, 'cred_detail.html', {'cred': cred, 'lastchange': lastchange, 'action': reverse('cred.views.delete', args=(cred_id,)), 'delete': True})


@login_required
def search(request):
    return render(request, 'cred_search.html', {})


@login_required
def tagadd(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('cred.views.list'))
    else:
        form = TagForm()

    return render(request, 'cred_tagedit.html', {'form': form})


@login_required
def tagedit(request, tag_id):
    tag = get_object_or_404(Tag, pk=tag_id)
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('cred.views.list'))
    else:
        form = TagForm(instance=tag)

    return render(request, 'cred_tagedit.html', {'form': form})


@login_required
def tagdelete(request, tag_id):
    tag = get_object_or_404(Tag, pk=tag_id)
    if request.method == 'POST':
        tag.delete()
        return HttpResponseRedirect(reverse('cred.views.tags'))
    return render(request, 'cred_tagdelete.html', {'t': tag})


@login_required
def addtoqueue(request, cred_id):
    cred = get_object_or_404(Cred, pk=cred_id)
    # Check user has perms (user must be member of the password owner group)
    if not cred.is_owned_by(request.user):
        raise Http404
    CredChangeQ.objects.add_to_changeq(cred)
    CredAudit(audittype=CredAudit.CREDSCHEDCHANGE, cred=cred, user=request.user).save()
    return HttpResponseRedirect(reverse('cred.views.list', args=('special', 'changeq')))


@login_required
def bulkdelete(request):
    todel = Cred.objects.filter(id__in=request.POST.getlist('credcheck'))
    for c in todel:
        if c.is_owned_by(request.user) and c.latest is None:
            CredAudit(audittype=CredAudit.CREDDELETE, cred=c, user=request.user).save()
            c.delete()

    redirect = request.POST.get('next', reverse('cred.views.list'))
    return HttpResponseRedirect(redirect)


@login_required
def bulkundelete(request):
    toundel = Cred.objects.filter(id__in=request.POST.getlist('credcheck'))
    for c in toundel:
        if c.is_owned_by(request.user):
            CredAudit(audittype=CredAudit.CREDADD, cred=c, user=request.user).save()
            c.is_deleted = False
            c.save()

    redirect = request.POST.get('next', reverse('cred.views.list'))
    return HttpResponseRedirect(redirect)


@login_required
def bulkaddtoqueue(request):
    tochange = Cred.objects.filter(id__in=request.POST.getlist('credcheck'))
    for c in tochange:
        if c.is_owned_by(request.user) and c.latest is None:
            CredAudit(audittype=CredAudit.CREDSCHEDCHANGE, cred=c, user=request.user).save()
            CredChangeQ.objects.add_to_changeq(c)

    redirect = request.POST.get('next', reverse('cred.views.list'))
    return HttpResponseRedirect(redirect)


@login_required
def bulktagcred(request):
    tochange = Cred.objects.filter(id__in=request.POST.getlist('credcheck'))
    tag = get_object_or_404(Tag, pk=request.POST.get('tag'))
    for c in tochange:
        if c.is_owned_by(request.user) and c.latest is None:
            CredAudit(audittype=CredAudit.CREDMETACHANGE, cred=c, user=request.user).save()
            c.tags.add(tag)

    redirect = request.POST.get('next', reverse('cred.views.list'))
    return HttpResponseRedirect(redirect)
