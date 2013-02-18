from django.conf.urls import patterns, include, url
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.models import User

urlpatterns = patterns('staff.views',
    # Views in views.py
    url(r'^$', 'home'),
    url(r'^userdetail/(?P<uid>\d+)/$','userdetail'),
) + patterns('',
    # Class based views
    url(r'^useredit/(?P<pk>\d+)/$',   staff_member_required(UpdateView.as_view(model=User, template_name='staff_useredit.html', success_url='/staff/'))),
    url(r'^userdelete/(?P<pk>\d+)/$', staff_member_required(DeleteView.as_view(model=User, template_name='staff_userdel.html',  success_url='/staff/'))),
    url(r'^useradd/$',                staff_member_required(CreateView.as_view(model=User, template_name='staff_useredit.html', success_url='/staff/'}),
)
