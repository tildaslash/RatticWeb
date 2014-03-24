from django.test import TestCase
from django.utils.unittest import skipIf
from cred.models import Cred
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.conf import settings

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
        self.assertEqual(cred['title'], 'dans id')
        self.assertEqual(cred['password'], 'CeidAcHuhy')
        self.assertEqual(sorted(cred['tags']), sorted(['Internet', 'picasa.com']))

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
            'tags': ['tag1', 'tag2'],
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


class StaffViewTests(TestCase):
    def setUp(self):
        self.data = TestData()

    def test_home(self):
        resp = self.data.staff.get(reverse('staff.views.home'))
        self.assertEqual(resp.status_code, 200)
        userlist = resp.context['userlist']
        grouplist = resp.context['grouplist']
        self.assertIn(self.data.unorm, userlist)
        self.assertIn(self.data.ustaff, userlist)
        self.assertIn(self.data.unobody, userlist)
        self.assertIn(self.data.group, grouplist)
        self.assertIn(self.data.othergroup, grouplist)

    @skipIf(settings.LDAP_ENABLED, 'Test does not apply on LDAP')
    def test_userdetail(self):
        resp = self.data.staff.get(reverse('staff.views.userdetail', args=(self.data.unobody.id,)))
        self.assertEqual(resp.status_code, 200)
        user = resp.context['viewuser']
        self.assertEqual(self.data.unobody.id, user.id)

    @skipIf(settings.LDAP_ENABLED, 'Test does not apply on LDAP')
    def test_groupadd(self):
        resp = self.data.staff.get(reverse('staff.views.groupadd'))
        self.assertEqual(resp.status_code, 200)
        form = resp.context['form']
        post = {}
        for i in form:
            if i.value() is not None:
                post[i.name] = i.value()
        post['name'] = 'Test Group'
        resp = self.data.staff.post(reverse('staff.views.groupadd'), post, follow=True)
        self.assertEqual(resp.status_code, 200)
        # Make sure we can get the object without exception
        Group.objects.get(name='Test Group')

    def test_groupdetail(self):
        resp = self.data.staff.get(reverse('staff.views.groupdetail',
            args=(self.data.group.id,)))
        self.assertEqual(resp.status_code, 200)
        group = resp.context['group']
        self.assertEqual(self.data.group.id, group.id)

    @skipIf(settings.LDAP_ENABLED, 'Test does not apply on LDAP')
    def test_groupdelete(self):
        resp = self.data.staff.get(reverse('staff.views.groupdelete',
            args=(self.data.othergroup.id,)))
        self.assertEqual(resp.status_code, 200)
        group = resp.context['group']
        self.assertEqual(self.data.othergroup.id, group.id)
        resp = self.data.staff.post(reverse('staff.views.groupdelete',
            args=(self.data.othergroup.id,)), follow=True)
        with self.assertRaises(Group.DoesNotExist):
            Group.objects.get(id=self.data.othergroup.id)

    @skipIf(settings.LDAP_ENABLED, 'Test does not apply on LDAP')
    def test_userdelete(self):
        resp = self.data.staff.get(reverse('staff.views.userdelete',
            args=(self.data.unobody.id,)))
        self.assertEqual(resp.status_code, 200)
        user = resp.context['viewuser']
        self.assertEqual(self.data.unobody.id, user.id)
        resp = self.data.staff.post(reverse('staff.views.userdelete',
            args=(self.data.unobody.id,)), follow=True)
        self.assertEqual(resp.status_code, 200)
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(id=self.data.unobody.id)

    def test_audit_by_cred(self):
        resp = self.data.staff.get(reverse('staff.views.audit_by_cred',
            args=(self.data.cred.id,)))
        self.assertEqual(resp.status_code, 200)
        cred = resp.context['cred']
        loglist = resp.context['logs'].object_list
        self.assertEqual(self.data.cred.id, cred.id)
        self.assertEqual(resp.context['type'], 'cred')
        self.assertIn(self.data.logadd, loglist)
        self.assertIn(self.data.logview, loglist)

    def test_audit_by_user(self):
        resp = self.data.staff.get(reverse('staff.views.audit_by_user',
            args=(self.data.ustaff.id,)))
        self.assertEqual(resp.status_code, 200)
        user = resp.context['loguser']
        loglist = resp.context['logs'].object_list
        self.assertEqual(self.data.ustaff.id, user.id)
        self.assertEqual(resp.context['type'], 'user')
        self.assertIn(self.data.logadd, loglist)
        self.assertIn(self.data.logview, loglist)

    def test_audit_by_days(self):
        resp = self.data.staff.get(reverse('staff.views.audit_by_days',
            args=(2,)))
        self.assertEqual(resp.status_code, 200)
        days_ago = resp.context['days_ago']
        loglist = resp.context['logs'].object_list
        self.assertEqual(int(days_ago), 2)
        self.assertEqual(resp.context['type'], 'time')
        self.assertIn(self.data.logadd, loglist)
        self.assertIn(self.data.logview, loglist)

    def test_audit_by_largedays(self):
        resp = self.data.staff.get(reverse('staff.views.audit_by_days',
            args=(9999999999999,)))
        self.assertEqual(resp.status_code, 200)
        days_ago = resp.context['days_ago']
        loglist = resp.context['logs'].object_list
        self.assertEqual(int(days_ago), 9999999999999)
        self.assertEqual(resp.context['type'], 'time')
        self.assertIn(self.data.logadd, loglist)
        self.assertIn(self.data.logview, loglist)

    @skipIf(settings.LDAP_ENABLED, 'Test does not apply on LDAP')
    def test_NewUser(self):
        resp = self.data.staff.get(reverse('user_add'))
        self.assertEqual(resp.status_code, 200)
        form = resp.context['form']
        post = {}
        for i in form:
            if i.value() is not None:
                post[i.name] = i.value()
        post['username'] = 'test_user'
        post['email'] = 'me@me.com'
        post['groups'] = self.data.othergroup.id
        post['newpass'] = 'crazypass'
        post['confirmpass'] = 'crazypass'
        resp = self.data.staff.post(reverse('user_add'), post, follow=True)
        with self.assertRaises(KeyError):
            print resp.context['form'].errors
        self.assertEqual(resp.status_code, 200)
        newuser = User.objects.get(username='test_user')
        self.assertEqual(newuser.email, 'me@me.com')
        self.assertTrue(newuser.check_password('crazypass'))
        self.assertIn(self.data.othergroup, newuser.groups.all())
        self.assertNotIn(self.data.group, newuser.groups.all())

    @skipIf(settings.LDAP_ENABLED, 'Test does not apply on LDAP')
    def test_UpdateUser(self):
        resp = self.data.staff.get(reverse('user_edit', args=(self.data.unobody.id,)))
        self.assertEqual(resp.status_code, 200)
        form = resp.context['form']
        post = {}
        for i in form:
            if i.value() is not None:
                post[i.name] = i.value()
        post['email'] = 'newemail@example.com'
        post['newpass'] = 'differentpass'
        post['confirmpass'] = 'differentpass'
        resp = self.data.staff.post(reverse('user_edit', args=(self.data.unobody.id,)), post, follow=True)
        self.assertEqual(resp.status_code, 200)
        newuser = User.objects.get(id=self.data.unobody.id)
        self.assertEqual(newuser.email, 'newemail@example.com')
        self.assertTrue(newuser.check_password('differentpass'))

    def test_credundelete(self):
        self.data.cred.delete()
        resp = self.data.staff.get(reverse('staff.views.credundelete', args=(self.data.cred.id,)))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['cred'], self.data.cred)
        resp = self.data.staff.post(reverse('staff.views.credundelete', args=(self.data.cred.id,)), follow=True)
        self.assertEqual(resp.status_code, 200)
        cred = Cred.objects.get(id=self.data.cred.id)
        self.assertFalse(cred.is_deleted)

StaffViewTests = override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))(StaffViewTests)
