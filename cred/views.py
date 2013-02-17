from django.shortcuts import render
from models import Cred

def list(request):
    cred = Cred.objects.filter(group__in=request.user.groups.all())
    return render(request, 'cred_list.html', {'credlist': cred})

