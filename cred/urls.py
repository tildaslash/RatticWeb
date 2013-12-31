from django.conf.urls import patterns, url

urlpatterns = patterns('cred.views',
    # New list views
    url(r'^list/$', 'list'),
    url(r'^list-by-(?P<cfilter>\w+)/(?P<value>\d+)/$', 'list'),
    url(r'^list-by-(?P<cfilter>\w+)/(?P<value>[^/]*)/$', 'list'),
    url(r'^list-by-(?P<cfilter>\w+)/(?P<value>[^/]*)/sort-(?P<sortdir>ascending|descending)-by-(?P<sort>\w+)/$', 'list'),
    url(r'^list-by-(?P<cfilter>\w+)/(?P<value>[^/]*)/sort-(?P<sortdir>ascending|descending)-by-(?P<sort>\w+)/page-(?P<page>\d+)/$', 'list'),

    # Search dialog for mobile
    url(r'^search/$', 'search'),

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

    # Adding to the change queue
    url(r'^addtoqueue/(?P<cred_id>\d+)/$', 'addtoqueue'),

    # Bulk views (for buttons on list page)
    url(r'^bulkaddtoqueue/$', 'bulkaddtoqueue'),
    url(r'^bulkdelete/$', 'bulkdelete'),
    url(r'^bulkundelete/$', 'bulkundelete'),
)
