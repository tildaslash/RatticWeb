from django.conf.urls import patterns, include, url

urlpatterns = patterns('cred.views',
    url(r'^list/$', 'list'),
    url(r'^detail/(?P<cred_id>\d+)/$', 'detail'),
    url(r'^edit/(?P<cred_id>\d+)/$', 'edit'),
    url(r'^delete/(?P<cred_id>\d+)/$', 'delete'),
    url(r'^add/$', 'add'),
    url(r'^catadd/$', 'catadd'),
    url(r'^catedit/(?P<cat_id>\d+)/$', 'catedit'),
    url(r'^catdelete/(?P<cat_id>\d+)/$', 'catdelete'),
)
