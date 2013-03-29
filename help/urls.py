from django.conf.urls import patterns, include, url

urlpatterns = patterns('help.views',
    url(r'^$', 'help_home'),
    url(r'^(?P<page>[\w]+)/$', 'help_markdown'),
    url(r'^(?P<oldpage>[\w]+)/(?P<newpage>[\w]+)/$', 'help_linkhelper'),
)
