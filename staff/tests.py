from django.test import TestCase, Client
from cred.models import Cred, Tag, CredChangeQ, CredAudit
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from time import sleep


class StaffViewTests(TestCase):
    def setUp(self):
        self.group = Group(name='testgroup')
        self.group.save()

        self.othergroup = Group(name='othergroup')
        self.othergroup.save()

        self.tag = Tag(name='tag')
        self.tag.save()

        self.unorm = User(username='norm', email='norm@example.com')
        self.unorm.set_password('password')
        self.unorm.save()
        self.unorm.groups.add(self.group)
        self.unorm.save()

        self.ustaff = User(username='staff', email='steph@example.com', is_staff=True)
        self.ustaff.set_password('password')
        self.ustaff.save()
        self.ustaff.groups.add(self.group)
        self.ustaff.save()

        self.unobody = User(username='nobody', email='nobody@example.com')
        self.unobody.set_password('password')
        self.unobody.save()

        self.norm = Client()
        self.norm.login(username='norm', password='password')
        self.staff = Client()
        self.staff.login(username='staff', password='password')
        self.nobody = Client()
        self.nobody.login(username='nobody', password='password')

        self.cred = Cred(title='secret', password='s3cr3t', group=self.group)
        self.cred.save()
        self.tagcred = Cred(title='tagged', password='t4gg3d', group=self.group)
        self.tagcred.save()
        self.tagcred.tags.add(self.tag)
        self.tagcred.save()

        CredChangeQ.objects.add_to_changeq(self.cred)

        self.logadd = CredAudit(audittype=CredAudit.CREDADD, cred=self.cred,
                user=self.ustaff)
        self.logview = CredAudit(audittype=CredAudit.CREDVIEW, cred=self.cred,
                user=self.ustaff)
        self.logadd.save()
        self.logview.save()

    def test_home(self):
        resp = self.staff.get(reverse('staff.views.home'))
        self.assertEqual(resp.status_code, 200)
        userlist = resp.context['userlist']
        grouplist = resp.context['grouplist']
        self.assertIn(self.unorm, userlist)
        self.assertIn(self.ustaff, userlist)
        self.assertIn(self.unobody, userlist)
        self.assertIn(self.group, grouplist)
        self.assertIn(self.othergroup, grouplist)

    def test_view_trash(self):
        self.cred.is_deleted = True
        self.cred.save()
        resp = self.staff.get(reverse('staff.views.view_trash'))
        self.assertEqual(resp.status_code, 200)
        credlist = resp.context['credlist'].object_list
        self.assertIn(self.cred, credlist)
        self.assertNotIn(self.tagcred, credlist)

    def test_userdetail(self):
        resp = self.staff.get(reverse('staff.views.userdetail', args=(self.unobody.id,)))
        self.assertEqual(resp.status_code, 200)
        user = resp.context['viewuser']
        self.assertEqual(self.unobody.id, user.id)

    def test_groupadd(self):
        resp = self.staff.get(reverse('staff.views.groupadd'))
        self.assertEqual(resp.status_code, 200)
        form = resp.context['form']
        post = {}
        for i in form:
            if i.value() is not None:
                post[i.name] = i.value()
        post['name'] = 'Test Group'
        resp = self.staff.post(reverse('staff.views.groupadd'), post, follow=True)
        self.assertEqual(resp.status_code, 200)
        newgroup = Group.objects.get(name='Test Group')

    def test_groupdetail(self):
        resp = self.staff.get(reverse('staff.views.groupdetail',
            args=(self.group.id,)))
        self.assertEqual(resp.status_code, 200)
        group = resp.context['group']
        self.assertEqual(self.group.id, group.id)

    def test_groupdelete(self):
        resp = self.staff.get(reverse('staff.views.groupdelete',
            args=(self.othergroup.id,)))
        self.assertEqual(resp.status_code, 200)
        group = resp.context['group']
        self.assertEqual(self.othergroup.id, group.id)
        resp = self.staff.post(reverse('staff.views.groupdelete',
            args=(self.othergroup.id,)), follow=True)
        with self.assertRaises(Group.DoesNotExist):
            delgroup = Group.objects.get(id=self.othergroup.id)

    def test_userdelete(self):
        resp = self.staff.get(reverse('staff.views.userdelete',
            args=(self.unobody.id,)))
        self.assertEqual(resp.status_code, 200)
        user = resp.context['viewuser']
        self.assertEqual(self.unobody.id, user.id)
        resp = self.staff.post(reverse('staff.views.userdelete',
            args=(self.unobody.id,)), follow=True)
        self.assertEqual(resp.status_code, 200)
        with self.assertRaises(User.DoesNotExist):
            deluser = User.objects.get(id=self.unobody.id)

    def test_audit_by_cred(self):
        resp = self.staff.get(reverse('staff.views.audit_by_cred',
            args=(self.cred.id,)))
        self.assertEqual(resp.status_code, 200)
        cred = resp.context['cred']
        loglist = resp.context['logs'].object_list
        self.assertEqual(self.cred.id, cred.id)
        self.assertEqual(resp.context['type'], 'cred')
        self.assertIn(self.logadd, loglist)
        self.assertIn(self.logview, loglist)

    def test_audit_by_user(self):
        resp = self.staff.get(reverse('staff.views.audit_by_user',
            args=(self.ustaff.id,)))
        self.assertEqual(resp.status_code, 200)
        user = resp.context['loguser']
        loglist = resp.context['logs'].object_list
        self.assertEqual(self.ustaff.id, user.id)
        self.assertEqual(resp.context['type'], 'user')
        self.assertIn(self.logadd, loglist)
        self.assertIn(self.logview, loglist)

    def test_audit_by_days(self):
        resp = self.staff.get(reverse('staff.views.audit_by_days',
            args=(2,)))
        self.assertEqual(resp.status_code, 200)
        days_ago = resp.context['days_ago']
        loglist = resp.context['logs'].object_list
        self.assertEqual(int(days_ago), 2)
        self.assertEqual(resp.context['type'], 'time')
        self.assertIn(self.logadd, loglist)
        self.assertIn(self.logview, loglist)

    def test_NewUser(self):
        resp = self.staff.get(reverse('user_add'))
        self.assertEqual(resp.status_code, 200)
        form = resp.context['form']
        post = {}
        for i in form:
            if i.value() is not None:
                post[i.name] = i.value()
        post['username'] = 'test_user'
        post['email'] = 'me@me.com'
        post['groups'] = self.othergroup.id
        post['newpass'] = 'crazypass'
        post['confirmpass'] = 'crazypass'
        resp = self.staff.post(reverse('user_add'), post, follow=True)
        with self.assertRaises(KeyError):
            print resp.context['form'].errors
        self.assertEqual(resp.status_code, 200)
        newuser = User.objects.get(username='test_user')
        self.assertEqual(newuser.email, 'me@me.com')
        self.assertTrue(newuser.check_password('crazypass'))
        self.assertIn(self.othergroup, newuser.groups.all())
        self.assertNotIn(self.group, newuser.groups.all())

    def test_UpdateUser(self):
        resp = self.staff.get(reverse('user_edit', args=(self.unobody.id,)))
        self.assertEqual(resp.status_code, 200)
        form = resp.context['form']
        post = {}
        for i in form:
            if i.value() is not None:
                post[i.name] = i.value()
        post['email'] = 'newemail@example.com'
        post['newpass'] = 'differentpass'
        post['confirmpass'] = 'differentpass'
        resp = self.staff.post(reverse('user_edit', args=(self.unobody.id,)), post, follow=True)
        self.assertEqual(resp.status_code, 200)
        newuser = User.objects.get(id=self.unobody.id)
        self.assertEqual(newuser.email, 'newemail@example.com')
        self.assertTrue(newuser.check_password('differentpass'))

    def test_import_from_keepass(self):
        gp = Group(name='KeepassImportTest')
        gp.save()
        self.ustaff.groups.add(gp)
        self.ustaff.save()

        resp = self.staff.get(reverse('staff.views.import_from_keepass'))
        self.assertEqual(resp.status_code, 200)
        form = resp.context['form']
        post = {}
        for i in form:
            if i.value() is not None:
                post[i.name] = i.value()
        post['password'] = 'test'
        post['group'] = gp.id
        with open('docs/keepass/test2.kdb') as fp:
            post['file'] = fp
            resp = self.staff.post(reverse('staff.views.import_from_keepass'), post, follow=True)
        self.assertEqual(resp.status_code, 200)
        newcred = Cred.objects.get(title='Google', group=gp)
        self.assertEqual(newcred.password, 'Q5CLQhLqI3CtKgK')
        self.assertEqual(newcred.tags.all()[0].name, 'Internet')

    def test_credundelete(self):
        self.cred.delete()
        resp = self.staff.get(reverse('staff.views.credundelete', args=(self.cred.id,)))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['cred'], self.cred)
        resp = self.staff.post(reverse('staff.views.credundelete', args=(self.cred.id,)), follow=True)
        self.assertEqual(resp.status_code, 200)
        cred = Cred.objects.get(id=self.cred.id)
        self.assertFalse(cred.is_deleted)


class StaffChangeAdviceTest(TestCase):
    def setUp(self):
        self.group = Group(name='testgroup')
        self.group.save()

        self.othergroup = Group(name='othergroup')
        self.othergroup.save()

        self.unorm = User(username='norm', email='norm@example.com')
        self.unorm.set_password('password')
        self.unorm.save()
        self.unorm.groups.add(self.group)
        self.unorm.save()

        self.ustaff = User(username='staff', email='steph@example.com', is_staff=True)
        self.ustaff.set_password('password')
        self.ustaff.save()
        self.ustaff.groups.add(self.group)
        self.ustaff.save()

        self.norm = Client()
        self.norm.login(username='norm', password='password')
        self.staff = Client()
        self.staff.login(username='staff', password='password')

        self.viewedcred = Cred(title='Viewed', password='s3cr3t', group=self.group)
        self.viewedcred.save()
        self.changedcred = Cred(title='Changed', password='t4gg3d', group=self.group)
        self.changedcred.save()

        CredAudit(audittype=CredAudit.CREDADD, cred=self.viewedcred, user=self.unorm).save()
        CredAudit(audittype=CredAudit.CREDADD, cred=self.changedcred, user=self.unorm).save()
        CredAudit(audittype=CredAudit.CREDVIEW, cred=self.viewedcred, user=self.unorm).save()
        CredAudit(audittype=CredAudit.CREDVIEW, cred=self.changedcred, user=self.unorm).save()
        CredAudit(audittype=CredAudit.CREDCHANGE, cred=self.changedcred, user=self.ustaff).save()

    def test_disable_user(self):
        resp = self.staff.get(reverse('staff.views.change_advice_by_user', args=(self.unorm.id,)))
        self.assertEqual(resp.status_code, 200)
        credlist = resp.context['creds']
        self.assertIn(self.viewedcred, credlist)
        self.assertNotIn(self.changedcred, credlist)

    def test_remove_group(self):
        resp = self.staff.get(reverse('staff.views.change_advice_by_user_and_group',
            args=(self.unorm.id, self.group.id)))
        self.assertEqual(resp.status_code, 200)
        credlist = resp.context['creds']
        self.assertIn(self.viewedcred, credlist)
        self.assertNotIn(self.changedcred, credlist)


StaffViewTests = override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))(StaffViewTests)
StaffChangeAdviceTest = override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))(StaffChangeAdviceTest)
