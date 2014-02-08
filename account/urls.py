from django.conf.urls import patterns, url
from django.conf import settings

from views import profile, newapikey, deleteapikey, RatticSessionDeleteView
from views import RatticTFADisableView, RatticTFABackupTokensView
from views import RatticTFASetupView

from two_factor.views import LoginView

urlpatterns = patterns('',
    url(r'^$', profile, {}),
    url(r'^newapikey/$', newapikey, {}),
    url(r'^deleteapikey/(?P<key_id>\d+)/$', deleteapikey, {}),

    url(r'^logout/$', 'django.contrib.auth.views.logout', {
        'next_page': settings.RATTIC_ROOT_URL}),

    # View to kill other sessions with
    url(r'^killsession/(?P<pk>\w+)/', RatticSessionDeleteView.as_view(), name='kill_session')

    # Two Factor Views
    url(r'^login/$', LoginView.as_view(), name='login'),
    url(r'^two_factor/disable/$', RatticTFADisableView.as_view(), name='tfa_disable'),
    url(r'^two_factor/backup/$', RatticTFABackupTokensView.as_view(), name='tfa_backup'),
    url(r'^two_factor/setup/$', RatticTFASetupView.as_view(), name='tfa_setup'),
)

# URLs we don't want enabled with LDAP
if not settings.LDAP_ENABLED:
    urlpatterns += (
        url(r'^reset/$', 'django.contrib.auth.views.password_reset', {
            'post_reset_redirect': '/account/reset/done/',
            'template_name': 'password_reset.html'
            }, name="password_reset"),

        url(r'^reset/done/$', 'django.contrib.auth.views.password_reset_done', {
            'template_name': 'password_reset_done.html'}),

        url(r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm', {
            'post_reset_redirect': '/',
            'template_name': 'password_reset_confirm.html'}),

        url(r'^changepass/$', 'django.contrib.auth.views.password_change', {
            'post_change_redirect': '/account/profile/',
            'template_name': 'account_changepass.html'}, name='password_change')
    )

# URLs we do want enabled with LDAP
if settings.LDAP_ENABLED and settings.AUTH_LDAP_ALLOW_PASSWORD_CHANGE:
    urlpatterns += patterns('',
        url(r'^changepass/$', 'account.views.ldap_password_change', {}, name='password_change')
    )
