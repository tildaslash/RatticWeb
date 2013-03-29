from django.conf.urls import patterns, include, url

urlpatterns = patterns('help.views',
    url(r'^$', 'home'),
    url(r'^(?P<page>[\w]+)/$', 'markdown'),
)
