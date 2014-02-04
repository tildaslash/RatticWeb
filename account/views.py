from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from account.models import ApiKey, ApiKeyForm
from models import UserProfileForm, LDAPPassChangeForm

from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from django.utils.timezone import now

from user_sessions.views import SessionDeleteView
from two_factor.utils import default_device
from two_factor.views import DisableView


@login_required
def profile(request):
    # Get a list of the users API Keys
    keys = ApiKey.objects.filter(user=request.user)
    try:
        backup_tokens = request.user.staticdevice_set.all()[0].token_set.count()
    except IndexError:
        backup_tokens = 0

    # Get a list of the users current sessions
    sessions = request.user.session_set.filter(expire_date__gt=now())

    # Get the current session key
    session_key = request.session.session_key

    # Process the form if we have data coming in
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
    else:
        form = UserProfileForm(instance=request.user.profile)

    # Show the template
    return render(request, 'account_profile.html', {
        'keys': keys,
        'sessions': sessions,
        'session_key': session_key,
        'form': form,
        'user': request.user,
        'default_device': default_device(request.user),
        'backup_tokens': backup_tokens,
    })


@login_required
def newapikey(request):
    if request.method == 'POST':
        newkey = ApiKey(user=request.user, active=True)
        form = ApiKeyForm(request.POST, instance=newkey)
        if form.is_valid():
            form.save()
        return render(request, 'account_viewapikey.html', {'key': newkey})
    else:
        form = ApiKeyForm()

    return render(request, 'account_newapikey.html', {'form': form})


@login_required
def deleteapikey(request, key_id):
    key = get_object_or_404(ApiKey, pk=key_id)

    if key.user != request.user:
        raise Http404

    if request.method == 'POST':
        key.delete()
        return HttpResponseRedirect(reverse('account.views.profile'))

    return render(request, 'account_deleteapikey.html', {'key': key})


# Stolen from django.contrib.auth.views
# modifed to support LDAP errors
@sensitive_post_parameters()
@login_required
def ldap_password_change(request,
                    template_name='account_changepass.html',
                    post_change_redirect='/account/profile/',
                    password_change_form=LDAPPassChangeForm,
                    current_app=None, extra_context=None):
    import ldap

    if post_change_redirect is None:
        post_change_redirect = reverse('django.contrib.auth.views.password_change_done')
    if request.method == "POST":
        form = password_change_form(user=request.user, data=request.POST)
        if form.is_valid():
            try:
                form.save()
                return HttpResponseRedirect(post_change_redirect)
            except ldap.LDAPError as e:
                return render(request, 'account_ldaperror.html', {
                    'desc': e.message['desc'],
                    'info': e.message['info'],
                })
    else:
        form = password_change_form(user=request.user)
    context = {
        'form': form,
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, template_name, context,
                            current_app=current_app)


class RatticSessionDeleteView(SessionDeleteView):
    def get_success_url(self):
        return reverse('account.views.profile')


class RatticTFADisableView(DisableView):
    template_name = 'account_tfa_disable.html'
