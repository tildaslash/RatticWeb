from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from tastypie.api import Api
from cred.api import CredResource, TagResource
from staff.api import GroupResource
from django.conf import settings

# Setup the API
v1_api = Api(api_name='v1')
v1_api.register(CredResource())
v1_api.register(TagResource())
v1_api.register(GroupResource())

# Setup the base paths for applications, and the API
base_urlpatterns = patterns('',
    # Apps:
    url(r'^$', 'ratticweb.views.home', name='home'),
    url(r'^account/', include('account.urls')),
    url(r'^cred/', include('cred.urls')),
    url(r'^staff/', include('staff.urls')),
    url(r'^help/', include('help.urls')),

    # API
    url(r'^api/', include(v1_api.urls)),

    # two Factor
    url(r'^', include('two_factor.urls', namespace='two_factor')),
)

# If in debug mode enable the Django admin interface
if settings.DEBUG:
    # Uncomment the next two lines to enable the admin:
    from django.contrib import admin
    admin.autodiscover()

    base_urlpatterns += patterns('',
        # Uncomment the admin/doc line below to enable admin documentation:
        url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

        # Uncomment the next line to enable the admin:
        url(r'^admin/', include(admin.site.urls)),
    )

# Strip any leading slash from the RATTIC_ROOT_URL
if settings.RATTIC_ROOT_URL[0] == '/':
    root = settings.RATTIC_ROOT_URL[1:]
else:
    root = settings.RATTIC_ROOT_URL

# Serve RatticDB from an alternate root if requested
urlpatterns = patterns('',
    url(r'^' + root, include(base_urlpatterns)),
)

# Serve the static files from the right location in dev mode
urlpatterns += staticfiles_urlpatterns()
