from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from cred.models import Cred
from ratticweb.tests.helper import TestData


class CredAttachmentTest(TestCase):
    def setUp(self):
        self.data = TestData()

    def test_upload_cred(self):
        # Load the edit form
        resp = self.data.norm.get(
            reverse('cred.views.edit', args=(self.data.cred.id, ))
        )
        self.assertEqual(resp.status_code, 200)

        # Get the data from the form to submit
        form = resp.context['form']
        post = form.initial
        del post['url']

        # Open a test file and upload it
        with open('docs/keepass/test2.kdb', 'r') as fp:
            post['attachment'] = fp

            resp = self.data.norm.post(
                reverse('cred.views.edit', args=(self.data.cred.id, )),
                post
            )
            self.assertEqual(resp.status_code, 302)

        # Get a new copy of the cred from the DB
        cred = Cred.objects.get(pk=self.data.cred.id)

        # Check it matches the test file
        with open('docs/keepass/test2.kdb', 'r') as fp:
            self.assertEqual(fp.read(), cred.attachment.read())


CredAttachmentTest = override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))(CredAttachmentTest)
