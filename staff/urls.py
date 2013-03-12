from django.conf.urls import patterns, include, url
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.models import User, Group
from views import NewUser, UpdateUser
from models import GroupForm

urlpatterns = patterns('staff.views',
    # Views in views.py
    url(r'^$', 'home'),
    url(r'^userdetail/(?P<uid>\d+)/$','userdetail'),
    url(r'^userdelete/(?P<uid>\d+)/$','userdelete'),
    url(r'^groupadd/$','groupadd'),
    url(r'^groupdetail/(?P<gid>\d+)/$','groupdetail'),
    url(r'^groupedit/(?P<gid>\d+)/$','groupedit'),
    url(r'^groupdelete/(?P<gid>\d+)/$','groupdelete'),
    url(r'^audit-by-cred/(?P<cred_id>\d+)/$','audit_by_cred'),
    url(r'^audit-by-user/(?P<user_id>\d+)/$','audit_by_user'),
    url(r'^audit-by-days/(?P<days_ago>\d+)/$','audit_by_days'),
    url(r'^change-advice-by-user/(?P<user_id>\d+)/$','change_advice_by_user'),
    url(r'^change-advice-by-user-and-group/(?P<user_id>\d+)/(?P<group_id>\d+)/$','change_advice_by_user_and_group'),
    url(r'^keepass-import/$','import_from_keepass'),
) + patterns('',
    # Custom class based views
    url(r'^useradd/$', NewUser.as_view()),
    url(r'^useredit/(?P<pk>\d+)/$', UpdateUser.as_view()),
)
