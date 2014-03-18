from user_sessions.utils.tests import Client
from django.core.urlresolvers import reverse
from django.test import TestCase


class HomepageTest(TestCase):
    def test_homepage_to_login_redirect(self):
        client = Client()
        response = client.get(reverse('home'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_admin_disabled(self):
        client = Client()
        response = client.get('/admin/')
        self.assertEqual(response.status_code, 404)
