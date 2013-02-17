from django.conf.urls import patterns, include, url

urlpatterns = patterns('cred.views',
    url(r'^list/$', 'list'),
    url(r'^detail/(?P<cred_id>\d+)/$', 'detail'),
)
