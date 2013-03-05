from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User, Group
from django.db.models import Q
from models import UserForm, GroupForm
from cred.models import CredAudit, Cred

@staff_member_required
def home(request):
    userlist = User.objects.all()
    grouplist = Group.objects.all()
    return render(request, 'staff_home.html', {'userlist': userlist, 'grouplist': grouplist})

# user detail
@staff_member_required
def userdetail(request, uid):
    user = get_object_or_404(User, pk=uid)
    credlogs = CredAudit.objects.filter(user=user, cred__group__in=request.user.groups.all())[:5]
    morelink = reverse('staff.views.audit_by_user', args=(user.id,))
    return render(request, 'staff_userdetail.html', {'viewuser' : user, 'credlogs':credlogs, 'morelink':morelink})

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

# group detail
@staff_member_required
def groupdetail(request, gid):
    group = get_object_or_404(Group, pk=gid)
    return render(request, 'staff_groupdetail.html', {'group' : group})

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

    return render(request, 'staff_groupedit.html', {'group' : group, 'form': form})

# group delete
@staff_member_required
def groupdelete(request, gid):
    group = get_object_or_404(Group, pk=gid)
    if request.method == 'POST':
        group.delete()
        return HttpResponseRedirect('/staff/')
    return render(request, 'staff_groupdetail.html', {'group' : group, 'delete':True})

# User delete
@staff_member_required
def userdelete(request, uid):
    user = get_object_or_404(User, pk=uid)
    if request.method == 'POST':
        user.delete()
        return HttpResponseRedirect('/staff/')
    return render(request, 'staff_userdetail.html', {'user' : user, 'delete':True})

# Credential view
@staff_member_required
def audit_by_cred(request, cred_id):
    logs = CredAudit.objects.filter(cred__id=cred_id)

    return render(request, 'staff_audit.html', { 'logs': logs, 'type': 'cred' })

@staff_member_required
def audit_by_user(request, user_id):
    logs = CredAudit.objects.filter(user__id=user_id)

    return render(request, 'staff_audit.html', { 'logs': logs, 'type': 'user' })

@staff_member_required
def change_advice_by_user_and_group(request, user_id, group_id):
    user = get_object_or_404(User, pk=user_id)
    get_groups = request.GET.getlist('group')

    # If we were given a group, use that, otherwise use all the users groups
    if group_id is not None:
        group = get_object_or_404(Group, pk=group_id)
        groups = (group,)
    elif len(get_groups) > 0:
        groups = Group.objects.filter(id__in=get_groups)
    else:
        groups = Group.objects.all()

    logs = CredAudit.objects.filter(
            # Get a list of changes done
            Q(cred__group__in=groups, audittype=CredAudit.CREDCHANGE) |
            # Combined with a list of view from this user
            Q(cred__group__in=groups, audittype=CredAudit.CREDVIEW, user=user)
            ).order_by('time')

    # Go through each entry in time order
    tochange = []
    for l in logs:
        # If this user viewed the password then change it
        if l.audittype == CredAudit.CREDVIEW:
            tochange.append(l.cred.id)
        # If there was a change done not by this user, dont change it
        if l.audittype == CredAudit.CREDCHANGE and l.user != user:
            if l.cred.id in tochange:
                tochange.remove(l.cred.id)

    # Fetch the list of credentials to change from the DB for the view
    creds = Cred.objects.filter(id__in=tochange)

    return render(request, 'staff_changeadvice.html', { 'creds': creds,
        'viewuser':user })

@staff_member_required
def change_advice_by_user(request, user_id):
    return change_advice_by_user_and_group(request, user_id, None)

# New User
class NewUser(FormView):
    form_class = UserForm
    template_name = 'staff_useredit.html'
    success_url = '/staff/'

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

# Edit Users
class UpdateUser(UpdateView):
    model = User
    form_class = UserForm
    template_name = 'staff_useredit.html'
    success_url = '/staff/'

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
                self.success_url = reverse('staff.views.change_advice_by_user',
                    args=(form.instance.id,)) + '?' + '&'.join(missing_groups)
        # If user is becoming inactive we want to redirect to change advice
        if 'is_active' in form.changed_data and not form.instance.is_active:
            self.success_url = reverse('staff.views.change_advice_by_user', args=(form.instance.id,))
        return super(UpdateUser, self).form_valid(form)

