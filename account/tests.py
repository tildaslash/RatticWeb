from django.test import TestCase
from django.test import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core.management import call_command
from tastypie.models import ApiKey


class AccountViewTests(TestCase):
    username = 'testinguser'
    password = 'testpass'
    testtags = 7
    testitems = 43

    def setUp(self):
        self.client = Client()
        self.u = User(username=self.username, email='you@example.com')
        self.u.set_password(self.password)
        self.u.save()
        profile = self.u.profile
        profile.items_per_page = self.testitems
        profile.save()
        self.client.login(username=self.username, password=self.password)
        # View the profile page to create an API key
        self.client.get(reverse('account.views.profile'))

    def test_profile_page(self):
        response = self.client.get(reverse('account.views.profile'))
        self.assertEqual(response.status_code, 200)
        user = response.context['user']
        self.assertEqual(user.profile.items_per_page, self.testitems)

    def test_newapikey_page(self):
        old = ApiKey.objects.get(user=self.u)
        response = self.client.get(reverse('account.views.newapikey'), follow=True)
        self.assertEqual(response.status_code, 200)
        new = ApiKey.objects.get(user=self.u)
        self.assertNotEqual(old.key, new.key)


class AccountCommandTests(TestCase):
    def test_command_demosetup(self):
        args=[]
        opts={}
        call_command('demosetup', *args, **opts)
        u = User.objects.get(username='admin')
        self.assertTrue(u.check_password('rattic'))
        self.assertTrue(u.is_staff)
