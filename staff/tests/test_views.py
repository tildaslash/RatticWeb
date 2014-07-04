from django.test import TestCase
from django.utils.unittest import skipIf
from cred.models import Cred
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.conf import settings

from ratticweb.tests.helper import TestData


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
        resp = self.data.staff.get(reverse('staff.views.audit',
            args=("cred", self.data.cred.id)))
        self.assertEqual(resp.status_code, 200)
        cred = resp.context['item']
        loglist = resp.context['logs'].object_list
        self.assertEqual(self.data.cred.id, cred.id)
        self.assertEqual(resp.context['by'], 'cred')
        self.assertIn(self.data.logadd, loglist)
        self.assertIn(self.data.logview, loglist)

    def test_audit_by_user(self):
        resp = self.data.staff.get(reverse('staff.views.audit',
            args=("user", self.data.ustaff.id)))
        self.assertEqual(resp.status_code, 200)
        user = resp.context['item']
        loglist = resp.context['logs'].object_list
        self.assertEqual(self.data.ustaff.id, user.id)
        self.assertEqual(resp.context['by'], 'user')
        self.assertIn(self.data.logadd, loglist)
        self.assertIn(self.data.logview, loglist)

    def test_audit_by_days(self):
        resp = self.data.staff.get(reverse('staff.views.audit',
            args=("days", 2)))
        self.assertEqual(resp.status_code, 200)
        days_ago = resp.context['item']
        loglist = resp.context['logs'].object_list
        self.assertEqual(days_ago, 2)
        self.assertEqual(resp.context['by'], 'days')
        self.assertIn(self.data.logadd, loglist)
        self.assertIn(self.data.logview, loglist)

    def test_audit_filtering(self):
        post = {
            'hide': 'A',
        }
        resp = self.data.staff.post(reverse('staff.views.audit',
            args=("days", 2)), post)
        self.assertEqual(resp.status_code, 200)
        days_ago = resp.context['item']
        loglist = resp.context['logs'].object_list
        self.assertEqual(days_ago, 2)
        self.assertEqual(resp.context['by'], 'days')
        self.assertNotIn(self.data.logadd, loglist)
        self.assertIn(self.data.logview, loglist)

    def test_audit_by_largedays(self):
        resp = self.data.staff.get(reverse('staff.views.audit',
            args=("days", 9999999999999)))
        self.assertEqual(resp.status_code, 200)
        days_ago = resp.context['item']
        loglist = resp.context['logs'].object_list
        self.assertEqual(days_ago, 9999999999999)
        self.assertEqual(resp.context['by'], 'days')
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
