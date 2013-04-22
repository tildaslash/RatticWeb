from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from tastypie.models import ApiKey
from models import UserProfileForm, LDAPPassChangeForm

from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse


@login_required
def profile(request):
    try:
        api_key = ApiKey.objects.get(user=request.user)
    except ObjectDoesNotExist:
        api_key = ApiKey.objects.create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
    else:
        form = UserProfileForm(instance=request.user.profile)

    return render(request, 'account_profile.html', {
        'form': form,
        'user': request.user,
        'apikey': api_key,
    })


@login_required
def newapikey(request):
    try:
        api_key = ApiKey.objects.get(user=request.user)
        api_key.delete()
        api_key = ApiKey.objects.create(user=request.user)
    except ObjectDoesNotExist:
        api_key = ApiKey.objects.create(user=request.user)

    return HttpResponseRedirect(reverse('account.views.profile'))


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
