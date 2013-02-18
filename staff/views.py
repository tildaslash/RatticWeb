from django.shortcuts import render, get_object_or_404
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User, Group
from models import UserForm

@staff_member_required
def home(request):
    userlist = User.objects.all() 
    grouplist = Group.objects.all()
    return render(request, 'staff_home.html', {'userlist': userlist, 'grouplist': grouplist})

# user detail
@staff_member_required
def userdetail(request, uid):
    user = get_object_or_404(User, pk=uid)
    return render(request, 'staff_userdetail.html', {'user' : user})

# group detail
@staff_member_required
def groupdetail(request, gid):
    group = get_object_or_404(Group, pk=gid)
    return render(request, 'staff_groupdetail.html', {'group' : group})

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

    # Create the user, set password to newpass
    def form_valid(self, form):
        if form.cleaned_data['newpass'] is not None:
            form.instance.set_password(form.cleaned_data['newpass'])
        return super(UpdateUser, self).form_valid(form)

