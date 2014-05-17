from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core import mail
from django.conf import settings
from django.test.utils import override_settings

from ratticweb.tests.helper import TestData

from cred.tasks import change_queue_emails


class CredEmailTests(TestCase):
    def setUp(self):
        self.data = TestData()

    def test_change_queue_email(self):
        change_queue_emails()

        print mail.outbox[0].body

        salutation = 'Hello ' + self.data.unorm.username + ',\n'
        credlink = 'https://' + settings.HOSTNAME + reverse('cred.views.detail', args=(self.data.cred.id, ))

        self.assertEqual('RatticDB - Passwords requiring changes', mail.outbox[0].subject)
        self.assertEqual(1, len(mail.outbox[0].to))
        self.assertEqual(self.data.unorm.email, mail.outbox[0].to[0])
        self.assertIn(salutation, mail.outbox[0].body)
        self.assertIn(credlink, mail.outbox[0].body)


CredEmailTests = override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))(CredEmailTests)
