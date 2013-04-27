from django.conf.urls import patterns, url

urlpatterns = patterns('cred.views',
    # New list views
    url(r'^list/$', 'list'),
    url(r'^list-by-(?P<cfilter>\w+)/(?P<value>\d+)/$', 'list'),
    url(r'^list-by-(?P<cfilter>\w+)/(?P<value>[\.\w\d]*)/$', 'list'),
    url(r'^list-by-(?P<cfilter>\w+)/(?P<value>[\.\w\d]*)/sort-(?P<sortdir>ascending|descending)-by-(?P<sort>\w+)/$', 'list'),
    url(r'^list-by-(?P<cfilter>\w+)/(?P<value>[\.\w\d]*)/sort-(?P<sortdir>ascending|descending)-by-(?P<sort>\w+)/page-(?P<page>\d+)/$', 'list'),

    # Single cred views
    url(r'^detail/(?P<cred_id>\d+)/$', 'detail'),
    url(r'^edit/(?P<cred_id>\d+)/$', 'edit'),
    url(r'^delete/(?P<cred_id>\d+)/$', 'delete'),
    url(r'^add/$', 'add'),

    # Tags
    url(r'^tags/$', 'tags'),
    url(r'^tagadd/$', 'tagadd'),
    url(r'^tagedit/(?P<tag_id>\d+)/$', 'tagedit'),
    url(r'^tagdelete/(?P<tag_id>\d+)/$', 'tagdelete'),

    # Should be up with the list views, but currently isn't
    url(r'^viewqueue/$', 'viewqueue'),

    # Adding to the change queue
    url(r'^addtoqueue/(?P<cred_id>\d+)/$', 'addtoqueue'),
    url(r'^bulkaddtoqueue/$', 'bulkaddtoqueue'),
)
