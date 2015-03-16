from django.test import TestCase
from django.core.files import File
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from ratticweb.tests.helper import TestData
from cred.models import Cred, Group
import os


here = os.path.abspath(os.path.dirname(__file__))
ssh_keys = os.path.join(here, "ssh_keys")


class CredSSHKeyTest(TestCase):
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
        del post['attachment']

        # Open a test file and upload it
        with open(os.path.join(ssh_keys, "1.pem"), 'r') as fp:
            post['ssh_key'] = fp

            resp = self.data.norm.post(
                reverse('cred.views.edit', args=(self.data.cred.id, )),
                post
            )
            self.assertEqual(resp.status_code, 302)

        # Get a new copy of the cred from the DB
        cred = Cred.objects.get(pk=self.data.cred.id)

        # Check it matches the test file
        with open(os.path.join(ssh_keys, "1.pem"), 'r') as fp:
            self.assertEqual(fp.read(), cred.ssh_key.read())

    def test_cred_fingerprint(self):
        group = Group.objects.create(name="group")
        with open(os.path.join(ssh_keys, "1.pem")) as fle:
            cred = Cred.objects.create(ssh_key=File(fle), group=group)
        cred.save()
        self.assertEqual(cred.ssh_key_fingerprint(), open(os.path.join(ssh_keys, "1.fingerprint")).read().strip())

    def test_cred_with_password_fingerprint(self):
        group = Group.objects.create(name="group")
        with open(os.path.join(ssh_keys, "2.pem")) as fle:
            with open(os.path.join(ssh_keys, "2.password")) as pfle:
                cred = Cred.objects.create(ssh_key=File(fle), group=group, password=pfle.read().strip())
        cred.save()
        self.assertEqual(cred.ssh_key_fingerprint(), open(os.path.join(ssh_keys, "2.fingerprint")).read().strip())


CredSSHKeyTest = override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))(CredSSHKeyTest)
