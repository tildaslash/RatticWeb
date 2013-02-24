from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect

def profile(request):
    return render(request, 'account_profile.html', {
        'user': request.user
    })

