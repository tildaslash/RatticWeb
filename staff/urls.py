from django.conf.urls import patterns, url
from django.conf import settings
from views import NewUser, UpdateUser

urlpatterns = patterns('staff.views',
    # Views in views.py
    url(r'^$', 'home'),

    # User/Group Management
    url(r'^userdetail/(?P<uid>\d+)/$', 'userdetail'),
    url(r'^removetoken/(?P<uid>\d+)/$', 'removetoken'),
    url(r'^groupdetail/(?P<gid>\d+)/$', 'groupdetail'),

    # Auditing
    url(r'^audit-by-(?P<by>\w+)/(?P<byarg>\d+)/$', 'audit'),

    # Importing
    url(r'^import/keepass/$', 'upload_keepass'),
    url(r'^import/process/$', 'import_overview'),
    url(r'^import/process/(?P<import_id>\d+)/$', 'import_process'),
    url(r'^import/process/(?P<import_id>\d+)/ignore/$', 'import_ignore'),

    # Undeletion
    url(r'^credundelete/(?P<cred_id>\d+)/$', 'credundelete'),
)

# URLs that we don't want with LDAP
if not settings.LDAP_ENABLED:
    urlpatterns += patterns('staff.views',
        # Group Management
        url(r'^groupadd/$', 'groupadd'),
        url(r'^groupedit/(?P<gid>\d+)/$', 'groupedit'),
        url(r'^groupdelete/(?P<gid>\d+)/$', 'groupdelete'),

        # User Management
        url(r'^useradd/$', NewUser.as_view(), name="user_add"),
        url(r'^useredit/(?P<pk>\d+)/$', UpdateUser.as_view(), name="user_edit"),
        url(r'^userdelete/(?P<uid>\d+)/$', 'userdelete'),
    )
