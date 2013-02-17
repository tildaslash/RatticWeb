from django.conf.urls import patterns, include, url
from django.contrib.auth.models import User

urlpatterns = patterns('staff.views',
    url(r'^$', 'home'),
    url(r'^userdetail/(?P<uid>\d+)/$','userdetail'),
) + patterns('django.views.generic.create_update',
    url(r'^useredit/(?P<object_id>\d+)/$', 'update_object', {'model': User, 'template_name': 'staff_useredit.html'}),
    url(r'^useradd/$', 'create_object', {'model': User, 'template_name': 'staff_useredit.html'}),
    url(r'^userdelete/(?P<object_id>\d+)/$', 'delete_object', {'model': User, 'template_name': 'staff_userdel.html', 'post_delete_redirect': '/staff'}),
)
