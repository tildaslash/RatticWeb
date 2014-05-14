from user_sessions.utils.tests import Client
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.test import TestCase


class ErrorTest(TestCase):
    @override_settings(DEBUG=False)
    def test_404_page(self):
        client = Client()
        response = client.get(reverse('home') + 'thisurldoesnotexist')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')
        self.assertTrue('rattic_icon' in response.context.keys())
