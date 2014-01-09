from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseRedirect, Http404
from django.views.generic.edit import UpdateView, FormView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User, Group
from django.conf import settings
from models import UserForm, GroupForm, KeepassImportForm
from cred.models import CredAudit, Cred, Tag
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

import datetime
from django.utils.timezone import now
from django.utils.timezone import utc


@staff_member_required
def home(request):
    userlist = User.objects.all()
    grouplist = Group.objects.all()
    return render(request, 'staff_home.html', {'userlist': userlist, 'grouplist': grouplist})


@staff_member_required
def userdetail(request, uid):
    user = get_object_or_404(User, pk=uid)
    if settings.LDAP_ENABLED:
        from django_auth_ldap.backend import LDAPBackend
        popuser = LDAPBackend().populate_user(user.username)
        if popuser is None:
            user.is_active = False
            user.save()
            return HttpResponseRedirect(reverse('cred.views.list',
                args=('changeadvice', user.id)))
    credlogs = CredAudit.objects.filter(user=user, cred__group__in=request.user.groups.all())[:5]
    morelink = reverse('staff.views.audit_by_user', args=(user.id,))
    return render(request, 'staff_userdetail.html', {'viewuser': user, 'credlogs': credlogs, 'morelink': morelink})


@staff_member_required
def groupadd(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
            request.user.groups.add(form.instance)
            return HttpResponseRedirect(reverse('staff.views.home'))
    else:
        form = GroupForm()

    return render(request, 'staff_groupedit.html', {'form': form})


@staff_member_required
def groupdetail(request, gid):
    group = get_object_or_404(Group, pk=gid)
    return render(request, 'staff_groupdetail.html', {'group': group})


@staff_member_required
def groupedit(request, gid):
    group = get_object_or_404(Group, pk=gid)
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('staff.views.home'))
    else:
        form = GroupForm(instance=group)

    return render(request, 'staff_groupedit.html', {'group': group, 'form': form})


@staff_member_required
def groupdelete(request, gid):
    group = get_object_or_404(Group, pk=gid)
    if request.method == 'POST':
        group.delete()
        return HttpResponseRedirect(reverse('staff.views.home'))
    return render(request, 'staff_groupdetail.html', {'group': group, 'delete': True})


@staff_member_required
def userdelete(request, uid):
    user = get_object_or_404(User, pk=uid)
    if request.method == 'POST':
        user.delete()
        return HttpResponseRedirect(reverse('staff.views.home'))
    return render(request, 'staff_userdetail.html', {'viewuser': user, 'delete': True})


@staff_member_required
def audit_by_cred(request, cred_id):
    cred = get_object_or_404(Cred, pk=cred_id)
    alllogs = CredAudit.objects.filter(cred=cred)

    paginator = Paginator(alllogs, request.user.profile.items_per_page)
    page = request.GET.get('page')

    try:
        logs = paginator.page(page)
    except PageNotAnInteger:
        logs = paginator.page(1)
    except EmptyPage:
        logs = paginator.page(paginator.num_pages)

    return render(request, 'staff_audit.html', {'logs': logs, 'type': 'cred', 'cred': cred})


@staff_member_required
def audit_by_user(request, user_id):
    loguser = get_object_or_404(User, pk=user_id)
    alllogs = CredAudit.objects.filter(user=loguser)

    paginator = Paginator(alllogs, request.user.profile.items_per_page)
    page = request.GET.get('page')

    try:
        logs = paginator.page(page)
    except PageNotAnInteger:
        logs = paginator.page(1)
    except EmptyPage:
        logs = paginator.page(paginator.num_pages)

    return render(request, 'staff_audit.html', {'logs': logs, 'type': 'user', 'loguser': loguser})


@staff_member_required
def audit_by_days(request, days_ago):
    try:
        delta = datetime.timedelta(days=int(days_ago))
        datefrom = now() - delta
    except OverflowError:
        datefrom = datetime.datetime(1970, 1, 1).replace(tzinfo=utc)
    alllogs = CredAudit.objects.filter(time__gte=datefrom)

    paginator = Paginator(alllogs, request.user.profile.items_per_page)
    page = request.GET.get('page')

    try:
        logs = paginator.page(page)
    except PageNotAnInteger:
        logs = paginator.page(1)
    except EmptyPage:
        logs = paginator.page(paginator.num_pages)

    return render(request, 'staff_audit.html', {'logs': logs, 'type': 'time', 'days_ago': days_ago})


class NewUser(FormView):
    form_class = UserForm
    template_name = 'staff_useredit.html'
    success_url = reverse_lazy('staff.views.home')

    # Staff access only
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(NewUser, self).dispatch(*args, **kwargs)

    # Create the user, set password to newpass
    def form_valid(self, form):
        user = form.save()
        user.set_password(form.cleaned_data['newpass'])
        user.save()
        return super(NewUser, self).form_valid(form)


class UpdateUser(UpdateView):
    model = User
    form_class = UserForm
    template_name = 'staff_useredit.html'
    success_url = reverse_lazy('staff.views.home')

    # Staff access only
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(UpdateUser, self).dispatch(*args, **kwargs)

    # If the password changed, set password to newpass
    def form_valid(self, form):
        if form.cleaned_data['newpass'] is not None and len(form.cleaned_data['newpass']) > 0:
            form.instance.set_password(form.cleaned_data['newpass'])
        # If user is having groups removed we want change advice for those
        # groups
        if form.instance.is_active and 'groups' in form.changed_data:
            # Get a list of the missing groups
            missing_groups = []
            for g in form.instance.groups.all():
                if g not in form.cleaned_data['groups']:
                    missing_groups.append('group=' + str(g.id))

            # The user may have just added groups
            if len(missing_groups) > 0:
                self.success_url = reverse('cred.views.list',
                        args=('changeadvice', form.instance.id)) + '?' + '&'.join(missing_groups)
        # If user is becoming inactive we want to redirect to change advice
        if 'is_active' in form.changed_data and not form.instance.is_active:
            self.success_url = reverse('cred.views.list', args=('changeadvice', form.instance.id))
        return super(UpdateUser, self).form_valid(form)


@staff_member_required
def import_from_keepass(request):
    if request.method == 'POST':
        form = KeepassImportForm(request.user, request.POST, request.FILES)
        if form.is_valid():
            group = form.cleaned_data['group']
            for e in form.cleaned_data['db']['entries']:
                cred = Cred(
                    title=e['title'],
                    username=e['username'],
                    password=e['password'],
                    description=e['description'],
                    group=group,
                )
                cred.save()
                CredAudit(audittype=CredAudit.CREDADD, cred=cred, user=request.user).save()
                for t in e['tags']:
                    (tag, create) = Tag.objects.get_or_create(name=t)
                    cred.tags.add(tag)

            return HttpResponseRedirect(reverse('staff.views.home'))
    else:
        form = KeepassImportForm(request.user)
    return render(request, 'staff_keepassimport.html', {'form': form})


@staff_member_required
def credundelete(request, cred_id):
    cred = get_object_or_404(Cred, pk=cred_id)

    try:
        lastchange = CredAudit.objects.filter(
            cred=cred,
            audittype__in=[CredAudit.CREDCHANGE, CredAudit.CREDADD],
        ).latest().time
    except CredAudit.DoesNotExist:
        lastchange = "Unknown (Logs deleted)"

    # Check user has perms
    if not cred.is_accessible_by(request.user):
        raise Http404
    if request.method == 'POST':
        CredAudit(audittype=CredAudit.CREDADD, cred=cred, user=request.user).save()
        cred.is_deleted = False
        cred.save()
        return HttpResponseRedirect(reverse('cred.views.list', args=('special', 'trash')))

    CredAudit(audittype=CredAudit.CREDVIEW, cred=cred, user=request.user).save()

    return render(request, 'cred_detail.html', {'cred': cred, 'lastchange': lastchange, 'action': reverse('cred.views.delete', args=(cred_id,)), 'undelete': True})
