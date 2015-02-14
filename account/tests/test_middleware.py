from django.test import TestCase, Client
from django.test.utils import override_settings
from django.utils.unittest import skipIf
from django.utils.timezone import now
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
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
        loginurl = reverse('login')
        self.client.post(loginurl, {
            'auth-username': self.username,
            'auth-password': self.password,
            'rattic_tfa_login_view-current_step': 'auth'
        })

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

    def test_session_kill(self):
        # Get the current session key
        oldkey = self.client.cookies[settings.SESSION_COOKIE_NAME].value

        # Kill the current session
        response = self.client.post(reverse('kill_session', args=(oldkey,)))

        # Check the response redirected to the login page
        profileurl = reverse('account.views.profile')
        self.assertRedirects(response, profileurl, 302, 302)

        # Check we have a new session
        newkey = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        self.assertNotEqual(oldkey, newkey)

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
        self.assertRedirects(resp, reverse('account.views.rattic_change_password'), status_code=302, target_status_code=200)
        profile.password_changed = now()
        profile.save()
        resp = self.client.get(reverse('account.views.profile'))
        self.assertEqual(resp.status_code, 200)

    @skipIf(settings.LDAP_ENABLED, 'Test does not apply on LDAP')
    def test_change_password(self):
        # Load the password change page
        response = self.client.get(reverse('account.views.rattic_change_password'))
        self.assertEqual(response.status_code, 200)

        # Prepare the POST data
        post = {
            'old_password': self.password,
            'new_password1': 'newpassword',
            'new_password2': 'newpassword',
        }
        response = self.client.post(
            reverse('account.views.rattic_change_password'),
            post,
            follow=True,
        )

        # Check we got a 200 response and the password got changed
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username=self.username)
        self.assertTrue(user.check_password('newpassword'))

    @skipIf(settings.LDAP_ENABLED, 'Test does not apply on LDAP')
    def test_initial_password(self):
        # Clear the users password
        user = User.objects.get(username=self.username)
        user.set_unusable_password()
        user.save()

        # Load the password change page
        response = self.client.get(reverse('account.views.rattic_change_password'))
        self.assertEqual(response.status_code, 200)

        # Prepare the POST data
        post = {
            'new_password1': 'newpassword',
            'new_password2': 'newpassword',
        }
        response = self.client.post(
            reverse('account.views.rattic_change_password'),
            post,
            follow=True,
        )

        # Check we got a 200 response and the password got changed
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username=self.username)
        self.assertTrue(user.check_password('newpassword'))


class AccountMiddlewareTests(TestCase):
    def setUp(self):
        self.unorm = User(username='norm', email='norm@example.com')
        self.unorm.set_password('password')
        self.normpass = 'password'
        self.unorm.save()

    def test_login(self):
        c = Client()
        resp = c.post(reverse('login'), {
            'auth-username': 'norm',
            'auth-password': 'password',
            'rattic_tfa_login_view-current_step': 'auth',
        })
        self.assertRedirects(resp, reverse('cred.views.list'), status_code=302, target_status_code=200)
        self.assertTemplateNotUsed(resp, 'account_tfa_login.html')

    def test_login_wrongpass(self):
        c = Client()
        resp = c.post(reverse('login'), {
            'auth-username': 'norm',
            'auth-password': 'wrongpassword',
            'rattic_tfa_login_view-current_step': 'auth',
        }, follow=False)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'account_tfa_login.html')

    @skipIf(settings.LDAP_ENABLED, 'Test does not apply on LDAP')
    def test_login_disabled(self):
        self.unorm.is_active = False
        self.unorm.save()
        c = Client()
        resp = c.post(reverse('login'), {
            'auth-username': 'norm',
            'auth-password': 'wrongpassword',
            'rattic_tfa_login_view-current_step': 'auth',
        }, follow=False)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'account_tfa_login.html')
