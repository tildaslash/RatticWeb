from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from tastypie.models import ApiKey
from models import UserProfileForm

def profile(request):
    try:
        api_key = ApiKey.objects.get(user=request.user)
    except ObjectDoesNotExist:
        api_key = ApiKey.objects.create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('account.views.profile'))
    else:
        form = UserProfileForm(instance=request.user.profile)

    return render(request, 'account_profile.html', {
        'form': form,
        'user': request.user,
        'apikey': api_key,
    })

def newapikey(request):
    try:
        api_key = ApiKey.objects.get(user=request.user)
        api_key.delete()
        api_key = ApiKey.objects.create(user=request.user)
    except ObjectDoesNotExist:
        api_key = ApiKey.objects.create(user=request.user)

    return HttpResponseRedirect('/account/profile/')

