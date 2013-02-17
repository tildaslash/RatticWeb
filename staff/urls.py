from django.conf.urls import patterns, include, url

urlpatterns = patterns('staff.views',
    url(r'^$', 'home'),
)
