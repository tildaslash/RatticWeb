from django.test import TestCase
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from ratticweb.tests.helper import TestData


class ImportTests(TestCase):
    def setUp(self):
        self.data = TestData()

        # We need a group to import into
        gp = Group(name='KeepassImportTest')
        gp.save()
        self.gp = gp
        self.data.ustaff.groups.add(gp)
        self.data.ustaff.save()

    def test_upload_keepass(self):
        # Fetch the initial form
        resp = self.data.staff.get(reverse('staff.views.upload_keepass'))
        self.assertEqual(resp.status_code, 200)

        # Fill out the form values
        post = {}
        post['password'] = 'test'
        post['group'] = self.gp.id

        # Upload a test keepass file
        with open('docs/keepass/test2.kdb') as fp:
            post['file'] = fp
            resp = self.data.staff.post(reverse('staff.views.upload_keepass'), post, follow=True)
        self.assertEqual(resp.status_code, 200)

        # Get the session data, and sort entries for determinism
        data = self.data.staff.session['imported_data']
        data['entries'].sort()

        # Check the group matches
        self.assertEqual(data['group'], self.gp.id)

        # Check the right credentials are in there
        cred = data['entries'][0]
        attcred = data['entries'][3]
        self.assertEqual(cred['title'], 'dans id')
        self.assertEqual(cred['password'], 'CeidAcHuhy')
        self.assertEqual(sorted(cred['tags']), sorted(['Internet', 'picasa.com']))
        self.assertEqual(attcred['filename'], 'test.txt')
        self.assertEqual(attcred['filecontent'], 'This is a test file.\n')

    def test_process_import_no_data(self):
        # With no data we expect a 404
        resp = self.data.staff.get(reverse('staff.views.process_import'))
        self.assertEqual(resp.status_code, 404)

    def test_process_import_last_entry(self):
        # Setup finished test data
        entries = []
        session = self.data.staff.session
        session['imported_data'] = {}
        session['imported_data']['group'] = self.gp.id
        session['imported_data']['entries'] = entries
        session.save()

        # Try to import
        resp = self.data.staff.get(reverse('staff.views.process_import'))

        # Check we were redirected home
        self.assertRedirects(resp, reverse('staff.views.home'), 302, 200)
        self.assertNotIn('imported_data', self.data.staff.session)

    def test_process_import_entry_import(self):
        # Setup session test data
        entry = {
            'title': 'Test',
            'username': 'dan',
            'description': '',
            'password': 'pass',
            'url': 'http://example.com/',
            'tags': ['tag1', 'tag2'],
            'filename': None,
            'filecontent': '',
        }
        entries = [entry, ]
        session = self.data.staff.session
        session['imported_data'] = {}
        session['imported_data']['group'] = self.gp.id
        session['imported_data']['entries'] = entries
        session.save()

        # Load the import screen
        resp = self.data.staff.get(reverse('staff.views.process_import'))

        # Check things worked
        self.assertIn('imported_data', self.data.staff.session)
        self.assertEquals(len(self.data.staff.session['imported_data']['entries']), 0)
        self.assertTemplateUsed(resp, 'staff_process_import.html')


ImportTests = override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))(ImportTests)
