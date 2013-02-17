from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.http import Http404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User, Group

@staff_member_required
def home(request):
    userlist = User.objects.all() 
    grouplist = Group.objects.all()
    return render(request, 'staff_home.html', {'userlist': userlist, 'grouplist': grouplist})
