from django.conf.urls import patterns, include, url

urlpatterns = patterns('cred.views',
    url(r'^list/$', 'list'),
    url(r'^list-by-tag/(?P<tag_id>\d+)/$', 'list_by_tag'),
    url(r'^list-by-search/(?P<search>\w+)/$', 'list_by_search'),
    url(r'^detail/(?P<cred_id>\d+)/$', 'detail'),
    url(r'^edit/(?P<cred_id>\d+)/$', 'edit'),
    url(r'^delete/(?P<cred_id>\d+)/$', 'delete'),
    url(r'^add/$', 'add'),
    url(r'^tags/$', 'tags'),
    url(r'^viewqueue/$', 'viewqueue'),
    url(r'^tagadd/$', 'tagadd'),
    url(r'^tagedit/(?P<tag_id>\d+)/$', 'tagedit'),
    url(r'^tagdelete/(?P<tag_id>\d+)/$', 'tagdelete'),
    url(r'^addtoqueue/(?P<cred_id>\d+)/$', 'addtoqueue'),
)
