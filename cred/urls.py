from django.conf.urls import patterns, url

urlpatterns = patterns('cred.views',
    # List views
    url(r'^list/$', 'list'),
    url(r'^list-by-tag/(?P<tag_id>\d+)/$', 'list_by_tag'),
    url(r'^list-by-group/(?P<group_id>\d+)/$', 'list_by_group'),
    url(r'^list-by-search/(?P<search>[\w\.]*)/$', 'list_by_search'),

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
