from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from tastypie.models import ApiKey

def profile(request):
    try:
        api_key = ApiKey.objects.get(user=request.user)
    except ObjectDoesNotExist:
        api_key = ApiKey.objects.create(user=request.user)

    return render(request, 'account_profile.html', {
        'user': request.user,
        'apikey': api_key,
    })

