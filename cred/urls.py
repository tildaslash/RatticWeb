from django.conf.urls import patterns, url
from django.conf import settings

urlpatterns = patterns('cred.views',
    # New list views
    url(r'^list/$', 'list'),
    url(r'^list-by-(?P<cfilter>\w+)/(?P<value>[^/]*)/$', 'list'),
    url(r'^list-by-(?P<cfilter>\w+)/(?P<value>[^/]*)/sort-(?P<sortdir>ascending|descending)-by-(?P<sort>\w+)/$', 'list'),
    url(r'^list-by-(?P<cfilter>\w+)/(?P<value>[^/]*)/sort-(?P<sortdir>ascending|descending)-by-(?P<sort>\w+)/page-(?P<page>\d+)/$', 'list'),

    # Search dialog for mobile
    url(r'^search/$', 'search'),

    # Single cred views
    url(r'^detail/(?P<cred_id>\d+)/$', 'detail'),
    url(r'^detail/(?P<cred_id>\d+)/download/$', 'downloadattachment'),
    url(r'^detail/(?P<cred_id>\d+)/ssh_key/$', 'downloadsshkey'),
    url(r'^edit/(?P<cred_id>\d+)/$', 'edit'),
    url(r'^delete/(?P<cred_id>\d+)/$', 'delete'),
    url(r'^add/$', 'add'),

    # Adding to the change queue
    url(r'^addtoqueue/(?P<cred_id>\d+)/$', 'addtoqueue'),

    # Bulk views (for buttons on list page)
    url(r'^addtoqueue/bulk/$', 'bulkaddtoqueue'),
    url(r'^delete/bulk/$', 'bulkdelete'),
    url(r'^undelete/bulk/$', 'bulkundelete'),
    url(r'^addtag/bulk/$', 'bulktagcred'),

    # Tags
    url(r'^tag/$', 'tags'),
    url(r'^tag/add/$', 'tagadd'),
    url(r'^tag/edit/(?P<tag_id>\d+)/$', 'tagedit'),
    url(r'^tag/delete/(?P<tag_id>\d+)/$', 'tagdelete'),
)

if not settings.RATTIC_DISABLE_EXPORT:
    urlpatterns += patterns('cred.views',
        # Export views
        url(r'^export.kdb$', 'download'),
        url(r'^export-by-(?P<cfilter>\w+)/(?P<value>[^/]*).kdb$', 'download'),
    )
