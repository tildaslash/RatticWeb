from django.test import TestCase, Client
from cred.models import Cred, Tag, CredChangeQ
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

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

StaffViewTests = override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))(StaffViewTests)

