from django.test import TestCase, Client
from models import Cred, Tag, CredChangeQ
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.test.utils import override_settings


class CredAccessTest(TestCase):
    def setUp(self):
        g = Group(name='h')
        g.save()

        c = Cred(title='testcred', password='1234', group=g)
        c.save()

        d = Cred(title='todelete', password='12345678', group=g)
        d.save()
        d.delete()

        u = User(username='dan')
        u.save()
        u.groups.add(g)
        u.save()

        f = User(username='fail')
        f.save()

        s = User(username='staff', is_staff=True)
        s.save()
        s.groups.add(g)
        s.save()

        self.c = c
        self.d = d
        self.u = u
        self.f = f
        self.s = s

    def test_cred_access(self):
        self.assertTrue(self.c.is_accessable_by(self.u))
        self.assertTrue(not self.c.is_accessable_by(self.f))

    def test_credlist_visible(self):
        self.assertTrue(self.c in Cred.objects.accessable(self.u))
        self.assertTrue(not self.c in Cred.objects.accessable(self.f))

    def test_deleted_access(self):
        self.assertTrue(self.d.is_accessable_by(self.s))
        self.assertTrue(not self.d.is_accessable_by(self.u))

    def test_deleted_visibility(self):
        self.assertTrue(self.d in Cred.objects.accessable(self.s, deleted=True))
        self.assertTrue(not self.d in Cred.objects.accessable(self.u, deleted=True))


class CredDeleteTest(TestCase):
    def setUp(self):
        g = Group(name='h')
        g.save()

        c = Cred(title='testcred', password='1234', group=g)
        c.save()

        self.c = c

    def test_delete(self):
        c = self.c

        c.delete()

        self.assertEqual(Cred.objects.get(id=c.id), c)
        self.assertTrue(c.is_deleted)

        test = False

        c.delete()

        try:
            Cred.objects.get(id=c.id)
        except Cred.DoesNotExist:
            test = True

        self.assertTrue(test)


class CredHistoryTest(TestCase):
    def setUp(self):
        g = Group(name='h')
        g.save()

        c = Cred(title='historycred', password='1234', group=g)
        c.save()

        self.c = c

    def test_history(self):
        c = self.c

        # Check that changes are in the history
        c.title = 'newtitle'
        c.save()

        hc = Cred.objects.filter(title='historycred', latest=c).count()
        self.assertEqual(hc, 1)

        # Check that there can be more than one history
        c.password = '9876'
        c.save()

        hc = c.history.all().count()
        self.assertEqual(hc, 2)

    def test_pk_stability(self):
        c = self.c

        # Check that the ID of the object doesn't change
        oldid = c.id
        c.url = 'http://www.google.com/'
        c.save()
        newid = c.id

        self.assertEqual(oldid, newid)


class CredViewTests(TestCase):
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
        self.ustaff.groups.add(self.othergroup)
        self.ustaff.save()

        self.nobody = User(username='nobody', email='nobody@example.com')
        self.nobody.set_password('password')
        self.nobody.save()

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

    def test_list_normal(self):
        resp = self.norm.get(reverse('cred.views.list'))
        self.assertEqual(resp.status_code, 200)
        credlist = resp.context['credlist'].object_list
        self.assertTrue(self.cred in credlist)

    def test_list_staff(self):
        resp = self.staff.get(reverse('cred.views.list'))
        self.assertEqual(resp.status_code, 200)
        credlist = resp.context['credlist'].object_list
        self.assertTrue(self.cred not in credlist)

    def test_list_by_tag_normal(self):
        resp = self.norm.get(reverse('cred.views.list_by_tag', args=(self.tag.id,)))
        self.assertEqual(resp.status_code, 200)
        credlist = resp.context['credlist'].object_list
        self.assertTrue(self.cred not in credlist)
        self.assertTrue(self.tagcred in credlist)

    def test_list_by_tag_staff(self):
        resp = self.staff.get(reverse('cred.views.list_by_tag', args=(self.tag.id,)))
        self.assertEqual(resp.status_code, 200)
        credlist = resp.context['credlist'].object_list
        self.assertTrue(self.cred not in credlist)
        self.assertTrue(self.tagcred not in credlist)

    def test_list_by_group_normal(self):
        resp = self.norm.get(reverse('cred.views.list_by_group', args=(self.group.id,)))
        self.assertEqual(resp.status_code, 200)
        credlist = resp.context['credlist'].object_list
        self.assertTrue(self.cred in credlist)
        self.assertTrue(self.tagcred in credlist)

    def test_list_by_group_staff(self):
        resp = self.staff.get(reverse('cred.views.list_by_group', args=(self.othergroup.id,)))
        self.assertEqual(resp.status_code, 200)
        credlist = resp.context['credlist'].object_list
        self.assertTrue(self.cred not in credlist)
        self.assertTrue(self.tagcred not in credlist)

    def test_list_by_group_nobody(self):
        resp = self.nobody.get(reverse('cred.views.list_by_group', args=(self.othergroup.id,)))
        self.assertEqual(resp.status_code, 404)

    def test_tags_normal(self):
        resp = self.norm.get(reverse('cred.views.tags'))
        self.assertEqual(resp.status_code, 200)
        taglist = resp.context['tags']
        self.assertTrue(self.tag in taglist)
        self.assertEqual(len(taglist), 1)

    def test_list_by_search_normal(self):
        resp = self.norm.get(reverse('cred.views.list_by_search', args=('tag',)))
        self.assertEqual(resp.status_code, 200)
        taglist = resp.context['tag']
        credlist = resp.context['credlist'].object_list
        self.assertTrue(self.tag in taglist)
        self.assertEqual(len(taglist), 1)
        self.assertTrue(self.tagcred in credlist)
        self.assertTrue(self.cred not in credlist)

    def test_detail_normal(self):
        resp = self.norm.get(reverse('cred.views.detail', args=(self.cred.id,)))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['cred'].id, self.cred.id)
        self.assertEqual(resp.context['credlogs'], None)
        resp = self.norm.get(reverse('cred.views.detail', args=(self.tagcred.id,)))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['cred'].id, self.tagcred.id)
        self.assertEqual(resp.context['credlogs'], None)

    def test_detail_staff(self):
        resp = self.staff.get(reverse('cred.views.detail', args=(self.cred.id,)))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['cred'].id, self.cred.id)
        self.assertNotEqual(resp.context['credlogs'], None)
        resp = self.staff.get(reverse('cred.views.detail', args=(self.tagcred.id,)))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['cred'].id, self.tagcred.id)
        self.assertNotEqual(resp.context['credlogs'], None)

    def test_detail_nobody(self):
        resp = self.nobody.get(reverse('cred.views.detail', args=(self.cred.id,)))
        self.assertEqual(resp.status_code, 404)
        resp = self.nobody.get(reverse('cred.views.detail', args=(self.tagcred.id,)))
        self.assertEqual(resp.status_code, 404)

    def test_add_normal(self):
        resp = self.norm.get(reverse('cred.views.add'))
        self.assertEqual(resp.status_code, 200)
        form = resp.context['form']
        self.assertTrue(not form.is_valid())
        resp = self.norm.post(reverse('cred.views.add'), {
            'title': 'New Credential',
            'password': 'A password',
            'group': self.group.id,
            'icon': form['icon'].value(),
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        newcred = Cred.objects.get(title='New Credential')
        self.assertEqual(newcred.password, 'A password')

    def test_edit_normal(self):
        resp = self.norm.get(reverse('cred.views.edit', args=(self.cred.id,)))
        self.assertEqual(resp.status_code, 200)
        form = resp.context['form']
        post = {}
        for i in form:
            if i.value() is not None:
                post[i.name] = i.value()
        post['title'] = 'New Title'
        resp = self.norm.post(reverse('cred.views.edit', args=(self.cred.id,)), post, follow=True)
        self.assertEqual(resp.status_code, 200)
        newcred = Cred.objects.get(id=self.cred.id)
        self.assertEqual(newcred.title, 'New Title')

    def test_edit_nobody(self):
        resp = self.nobody.get(reverse('cred.views.edit', args=(self.cred.id,)))
        self.assertEqual(resp.status_code, 404)

    def test_delete_norm(self):
        resp = self.norm.get(reverse('cred.views.delete', args=(self.cred.id,)))
        self.assertEqual(resp.status_code, 200)
        resp = self.norm.post(reverse('cred.views.delete', args=(self.cred.id,)))
        delcred = Cred.objects.get(id=self.cred.id)
        self.assertTrue(delcred.is_deleted)

    def test_delete_staff(self):
        resp = self.staff.get(reverse('cred.views.delete', args=(self.cred.id,)))
        self.assertEqual(resp.status_code, 200)
        resp = self.staff.post(reverse('cred.views.delete', args=(self.cred.id,)), follow=True)
        self.assertEqual(resp.status_code, 200)
        delcred = Cred.objects.get(id=self.cred.id)
        self.assertTrue(delcred.is_deleted)

    def test_delete_nobody(self):
        resp = self.nobody.get(reverse('cred.views.delete', args=(self.cred.id,)))
        self.assertEqual(resp.status_code, 404)
        resp = self.nobody.post(reverse('cred.views.delete', args=(self.cred.id,)), follow=True)
        self.assertEqual(resp.status_code, 404)
        delcred = Cred.objects.get(id=self.cred.id)
        self.assertFalse(delcred.is_deleted)

    def test_tagadd_normal(self):
        resp = self.norm.get(reverse('cred.views.tagadd'))
        self.assertEqual(resp.status_code, 200)
        form = resp.context['form']
        post = {}
        for i in form:
            if i.value() is not None:
                post[i.name] = i.value()
        post['name'] = 'New Tag'
        resp = self.norm.post(reverse('cred.views.tagadd'), post, follow=True)
        self.assertEqual(resp.status_code, 200)
        newcred = Tag.objects.get(name='New Tag')

    def test_tagedit_normal(self):
        resp = self.norm.get(reverse('cred.views.tagedit', args=(self.tag.id,)))
        self.assertEqual(resp.status_code, 200)
        form = resp.context['form']
        post = {}
        for i in form:
            if i.value() is not None:
                post[i.name] = i.value()
        post['name'] = 'A Tag'
        resp = self.norm.post(reverse('cred.views.tagedit', args=(self.tag.id,)), post, follow=True)
        self.assertEqual(resp.status_code, 200)
        newtag = Tag.objects.get(name='A Tag')
        self.assertEqual(newtag.id, self.tag.id)

    def test_tagdelete_normal(self):
        resp = self.norm.get(reverse('cred.views.tagdelete', args=(self.tag.id,)))
        self.assertEqual(resp.status_code, 200)
        resp = self.staff.post(reverse('cred.views.tagdelete', args=(self.tag.id,)), follow=True)
        self.assertEqual(resp.status_code, 200)
        with self.assertRaises(Tag.DoesNotExist):
            deltag = Tag.objects.get(id=self.tag.id)

    def test_viewqueue_normal(self):
        resp = self.norm.get(reverse('cred.views.viewqueue'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['queue']), 1)
        self.assertEqual(resp.context['queue'][0].cred.id, self.cred.id)

    def test_viewqueue_nobody(self):
        resp = self.nobody.get(reverse('cred.views.viewqueue'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['queue']), 0)

    def test_addtoqueuestaff(self):
        resp = self.staff.get(reverse('cred.views.addtoqueue',
            args=(self.tagcred.id,)), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(self.tagcred.on_changeq())

CredViewTests = override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))(CredViewTests)
