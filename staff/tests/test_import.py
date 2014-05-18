from django.test import TestCase
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from ratticweb.tests.helper import TestData
from cred.models import Cred


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
        cred = filter(lambda x: x['title'] == 'dans id', data['entries'])[0]
        self.assertEqual(cred['title'], 'dans id')
        self.assertEqual(cred['password'], 'CeidAcHuhy')
        self.assertEqual(sorted(cred['tags']), sorted(['Internet', 'picasa.com']))

        # Check for attachments
        attcred = filter(lambda x: x['title'] == 'Attachment Test', data['entries'])[0]
        self.assertEqual(attcred['filename'], 'test.txt')
        self.assertEqual(attcred['filecontent'], 'This is a test file.\n')

    def test_process_import_no_data(self):
        # With no data we expect a 404
        resp = self.data.staff.get(reverse('staff.views.import_overview'))
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
        resp = self.data.staff.get(reverse('staff.views.import_overview'))

        # Check we were redirected home
        self.assertRedirects(resp, reverse('staff.views.home'), 302, 200)
        self.assertNotIn('imported_data', self.data.staff.session)

    def test_process_import_entry_ignore(self):
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
        session = self.data.staff.session
        session['imported_data'] = {}
        session['imported_data']['group'] = self.gp.id
        session['imported_data']['entries'] = [entry, ]
        session.save()

        # Load the import screen
        resp = self.data.staff.get(reverse('staff.views.import_ignore', args=(0, )))

        # Check things worked
        self.assertRedirects(resp, reverse('staff.views.import_overview'), 302, 302)
        self.assertNotIn('imported_data', self.data.staff.session)

    def test_process_import_entry_import(self):
        # Setup session test data
        entry = {
            'title': 'TestImportFunction',
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
        resp = self.data.staff.get(reverse('staff.views.import_process', args=(0, )))

        # Check things worked
        self.assertTemplateUsed(resp, 'staff_import_process.html')
        self.assertTrue(resp.context['form'].is_valid())

        # Perform the save
        post = {}
        for i in resp.context['form']:
            if i.value() is not None:
                post[i.name] = i.value()
        resp = self.data.staff.post(
            reverse('staff.views.import_process', args=(0, )),
            post,
        )

        # Test the results
        self.assertRedirects(resp, reverse('staff.views.import_overview'), 302, 302)
        c = Cred.objects.get(title='TestImportFunction')
        self.assertEquals(c.url, 'http://example.com/')
        self.assertEquals(c.password, 'pass')


ImportTests = override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))(ImportTests)
