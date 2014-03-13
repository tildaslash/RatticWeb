from django.test import TestCase, Client
from django.test.utils import override_settings
from django.utils.unittest import skipIf
from django.utils.timezone import now
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core.management import call_command
from django.conf import settings

from datetime import timedelta

from account.models import ApiKey


class AccountViewTests(TestCase):
    username = 'testinguser'
    password = 'testpass'
    testtags = 7
    testitems = 43

    def setUp(self):
        # Make user
        self.u = User(username=self.username, email='you@example.com')
        self.u.set_password(self.password)
        self.u.save()

        # Setup their profile
        profile = self.u.profile
        profile.items_per_page = self.testitems
        profile.save()

        # Log them in
        self.client = Client()
        loginurl = reverse('django.contrib.auth.views.login')
        self.client.post(loginurl, {'username': self.username, 'password': self.password})

        # View the profile page to create an API key
        self.client.get(reverse('account.views.profile'))

    def test_api_key_mgmt(self):
        resp = self.client.post(reverse('account.views.newapikey'), {'name': 'testing'})
        keyval = resp.context['key'].key
        testkey = ApiKey.objects.get(user=self.u, key=keyval)
        self.assertEqual(testkey.name, 'testing')
        resp = self.client.post(reverse('account.views.deleteapikey', args=(testkey.id,)))
        with self.assertRaises(ApiKey.DoesNotExist):
            ApiKey.objects.get(user=self.u, key=keyval)

    def test_profile_page(self):
        response = self.client.get(reverse('account.views.profile'))
        self.assertEqual(response.status_code, 200)
        user = response.context['user']
        self.assertEqual(user.profile.items_per_page, self.testitems)

    @skipIf(settings.LDAP_ENABLED, 'Test does not apply on LDAP')
    def test_disable_during_login(self):
        response = self.client.get(reverse('account.views.profile'))
        self.assertEqual(response.status_code, 200)
        self.u.is_active=False
        self.u.save()
        response = self.client.get(reverse('account.views.profile'))
        self.assertNotEqual(response.status_code, 200)

    @skipIf(settings.LDAP_ENABLED, 'Test does not apply on LDAP')
    @override_settings(PASSWORD_EXPIRY=timedelta(days=5))
    def test_password_expiry(self):
        profile = self.u.profile
        profile.password_changed = now() - timedelta(days=6)
        profile.save()
        resp = self.client.get(reverse('account.views.profile'), follow=True)
        self.assertRedirects(resp, reverse('django.contrib.auth.views.password_change'), status_code=302, target_status_code=200)
        profile.password_changed = now()
        profile.save()
        resp = self.client.get(reverse('account.views.profile'))
        self.assertEqual(resp.status_code, 200)


class AccountCommandTests(TestCase):
    def test_command_demosetup(self):
        args=[]
        opts={}
        call_command('demosetup', *args, **opts)
        u = User.objects.get(username='admin')
        self.assertTrue(u.check_password('rattic'))
        self.assertTrue(u.is_staff)


class AccountMiddlewareTests(TestCase):
    def setUp(self):
        self.unorm = User(username='norm', email='norm@example.com')
        self.unorm.set_password('password')
        self.normpass = 'password'
        self.unorm.save()

    def test_login(self):
        c = Client()
        resp = c.post(reverse('django.contrib.auth.views.login'), {
            'username': 'norm',
            'password': 'password',
        })
        self.assertRedirects(resp, reverse('cred.views.list'), status_code=302, target_status_code=200)
        self.assertTemplateNotUsed(resp, 'account_login.html')

    def test_login_wrongpass(self):
        c = Client()
        resp = c.post(reverse('django.contrib.auth.views.login'), {
            'username': 'norm',
            'password': 'wrongpassword',
        }, follow=False)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'account_login.html')

    @skipIf(settings.LDAP_ENABLED, 'Test does not apply on LDAP')
    def test_login_disabled(self):
        self.unorm.is_active = False
        self.unorm.save()
        c = Client()
        resp = c.post(reverse('django.contrib.auth.views.login'), {
            'username': 'norm',
            'password': 'wrongpassword',
        }, follow=False)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'account_login.html')
