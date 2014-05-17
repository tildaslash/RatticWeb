from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from cStringIO import StringIO
from keepassdb import Database

from cred.models import CredAudit

from ratticweb.tests.helper import TestData


class CredExportTests(TestCase):
    def setUp(self):
        self.data = TestData()

    def test_cred_export(self):
        # Grab the file
        data = {
            'password': 'testpass',
        }
        resp = self.data.norm.post(reverse('cred.views.download'), data)

        # Check for the right headers
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['content-type'], 'application/x-keepass')
        self.assertRegexpMatches(resp['content-disposition'], 'attachment; filename=\w+\.\w+')

        # Check the DB we got
        keepassdb = StringIO(resp.content)
        db = Database(keepassdb, 'testpass')
        testcred = filter(lambda x: x.title == 'secret', db.entries)[0]
        self.assertEqual(testcred.username, 'peh!')
        self.assertEqual(testcred.password, 's3cr3t')

        # Check the audit log
        CredAudit.objects.get(
            cred=self.data.cred.id,
            user=self.data.unorm.id,
            audittype=CredAudit.CREDEXPORT,
        )


CredExportTests = override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))(CredExportTests)
