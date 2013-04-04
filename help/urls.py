from django.conf.urls import patterns, url

urlpatterns = patterns('help.views',
    url(r'^$', 'home'),
    url(r'^(?P<page>[\w]+)/$', 'markdown'),
)
