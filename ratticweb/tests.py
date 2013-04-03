from django.test import TestCase
from django.test import Client
from django.core.urlresolvers import reverse


class HomepageTest(TestCase):
    def test_homepage_to_login_redirect(self):
        client = Client()
        response = client.get(reverse('home'), follow=True)
        self.assertTrue(response.redirect_chain[0][0].endswith(reverse('django.contrib.auth.views.login')))
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.status_code, 200)

    def test_admin_disabled(self):
        client = Client()
        response = client.get('/admin/')
        self.assertEqual(response.status_code, 404)
