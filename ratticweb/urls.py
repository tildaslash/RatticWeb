from django.conf.urls import patterns, include, url
from tastypie.api import Api
from cred.api import CredResource, TagResource
from staff.api import GroupResource
from django.conf import settings

v1_api = Api(api_name='v1')
v1_api.register(CredResource())
v1_api.register(TagResource())
v1_api.register(GroupResource())

urlpatterns = patterns('',
    # Apps:
    url(r'^$', 'ratticweb.views.home', name='home'),
    url(r'^account/', include('account.urls')),
    url(r'^cred/', include('cred.urls')),
    url(r'^staff/', include('staff.urls')),

    # API
    url(r'^api/', include(v1_api.urls)),
)

if settings.DEBUG == True:
    # Uncomment the next two lines to enable the admin:
    from django.contrib import admin
    admin.autodiscover()

    urlpatterns += patterns('',
        # Uncomment the admin/doc line below to enable admin documentation:
        url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

        # Uncomment the next line to enable the admin:
        url(r'^admin/', include(admin.site.urls)),
    )

