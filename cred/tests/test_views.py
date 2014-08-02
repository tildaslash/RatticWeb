# -*- coding: utf-8 -*-
from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from cred.models import Cred, Tag
from ratticweb.tests.helper import TestData


class CredViewTests(TestCase):
    def setUp(self):
        self.data = TestData()

    def test_list_normal(self):
        resp = self.data.norm.get(reverse('cred.views.list'))
        self.assertEqual(resp.status_code, 200)
        credlist = resp.context['credlist'].object_list
        self.assertTrue(self.data.cred in credlist)

    def test_list_sorting(self):
        resp = self.data.norm.get(reverse('cred.views.list',
                args=('special', 'all', 'ascending', 'title', 1)))
        self.assertEqual(resp.status_code, 200)
        credlist = resp.context['credlist'].object_list
        self.assertTrue(self.data.cred in credlist)

    def test_list_staff(self):
        resp = self.data.staff.get(reverse('cred.views.list'))
        self.assertEqual(resp.status_code, 200)
        credlist = resp.context['credlist'].object_list
        self.assertTrue(self.data.cred not in credlist)

    def test_list_trash_normal(self):
        self.data.cred.delete()
        resp = self.data.norm.get(reverse('cred.views.list', args=('special', 'trash')))
        self.assertEqual(resp.status_code, 200)
        credlist = resp.context['credlist'].object_list
        self.assertTrue(self.data.cred not in credlist)

    def test_list_trash_staff(self):
        self.data.cred.delete()
        self.data.ustaff.groups.add(self.data.group)
        resp = self.data.staff.get(reverse('cred.views.list', args=('special', 'trash')))
        self.assertEqual(resp.status_code, 200)
        credlist = resp.context['credlist'].object_list
        self.assertTrue(self.data.cred in credlist)

    def test_list_changeq_normal(self):
        self.data.cred.delete()
        resp = self.data.norm.get(reverse('cred.views.list', args=('special', 'changeq')))
        self.assertEqual(resp.status_code, 200)
        credlist = resp.context['credlist'].object_list
        self.assertTrue(self.data.cred not in credlist)

    def test_list_by_tag_normal(self):
        resp = self.data.norm.get(reverse('cred.views.list', args=('tag', self.data.tag.id)))
        self.assertEqual(resp.status_code, 200)
        credlist = resp.context['credlist'].object_list
        self.assertTrue(self.data.cred not in credlist)
        self.assertTrue(self.data.tagcred in credlist)

    def test_list_by_tag_staff(self):
        resp = self.data.staff.get(reverse('cred.views.list', args=('tag', self.data.tag.id)))
        self.assertEqual(resp.status_code, 200)
        credlist = resp.context['credlist'].object_list
        self.assertTrue(self.data.cred not in credlist)
        self.assertTrue(self.data.tagcred not in credlist)

    def test_list_by_group_normal(self):
        resp = self.data.norm.get(reverse('cred.views.list', args=('group', self.data.group.id)))
        self.assertEqual(resp.status_code, 200)
        credlist = resp.context['credlist'].object_list
        self.assertTrue(self.data.cred in credlist)
        self.assertTrue(self.data.tagcred in credlist)

    def test_list_by_group_staff(self):
        resp = self.data.staff.get(reverse('cred.views.list', args=('group', self.data.othergroup.id)))
        self.assertEqual(resp.status_code, 200)
        credlist = resp.context['credlist'].object_list
        self.assertTrue(self.data.cred not in credlist)
        self.assertTrue(self.data.tagcred not in credlist)

    def test_list_by_group_nobody(self):
        resp = self.data.nobody.get(reverse('cred.views.list', args=('group', self.data.othergroup.id)))
        self.assertEqual(resp.status_code, 404)

    def test_list_by_changeadvice_disable_user(self):
        resp = self.data.staff.get(reverse('cred.views.list', args=('changeadvice', self.data.unorm.id)))
        self.assertEqual(resp.status_code, 200)
        credlist = resp.context['credlist'].object_list
        self.assertIn(self.data.viewedcred, credlist)
        self.assertNotIn(self.data.changedcred, credlist)

    def test_list_by_changeadvice_user_added(self):
        resp = self.data.staff.get(reverse('cred.views.list', args=('changeadvice', self.data.unobody.id)))
        self.assertEqual(resp.status_code, 200)
        credlist = resp.context['credlist'].object_list
        self.assertIn(self.data.viewedcred, credlist)

    def test_list_by_changeadvice_remove_group(self):
        resp = self.data.staff.get(reverse('cred.views.list', args=('changeadvice', self.data.unorm.id)) + '?group=%s' % self.data.group.id)
        self.assertEqual(resp.status_code, 200)
        credlist = resp.context['credlist'].object_list
        self.assertIn(self.data.viewedcred, credlist)
        self.assertNotIn(self.data.changedcred, credlist)

    def test_tags_normal(self):
        resp = self.data.norm.get(reverse('cred.views.tags'))
        self.assertEqual(resp.status_code, 200)
        taglist = resp.context['tags']
        self.assertTrue(self.data.tag in taglist)
        self.assertEqual(len(taglist), 1)

    def test_list_by_search_normal(self):
        resp = self.data.norm.get(reverse('cred.views.list', args=('search', 'tag')))
        self.assertEqual(resp.status_code, 200)
        credlist = resp.context['credlist'].object_list
        self.assertTrue(self.data.tagcred in credlist)
        self.assertTrue(self.data.cred not in credlist)

    def test_list_by_search_unicode(self):
        resp = self.data.norm.get(reverse('cred.views.list', args=('search', 'ö')))
        self.assertEqual(resp.status_code, 200)
        credlist = resp.context['credlist'].object_list
        self.assertTrue(self.data.tagcred not in credlist)
        self.assertTrue(self.data.cred not in credlist)

    def test_detail_normal(self):
        resp = self.data.norm.get(reverse('cred.views.detail', args=(self.data.cred.id,)))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['cred'].id, self.data.cred.id)
        self.assertEqual(resp.context['credlogs'], None)
        resp = self.data.norm.get(reverse('cred.views.detail', args=(self.data.tagcred.id,)))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['cred'].id, self.data.tagcred.id)
        self.assertEqual(resp.context['credlogs'], None)

    def test_detail_markdown(self):
        resp = self.data.norm.get(reverse('cred.views.detail', args=(self.data.markdowncred.id,)))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['cred'].id, self.data.markdowncred.id)
        self.assertEqual(resp.context['credlogs'], None)
        self.assertContains(resp, "<h1>Test</h1>", html=True, count=1)

    def test_detail_staff(self):
        resp = self.data.staff.get(reverse('cred.views.detail', args=(self.data.cred.id,)))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['cred'].id, self.data.cred.id)
        self.assertNotEqual(resp.context['credlogs'], None)
        resp = self.data.staff.get(reverse('cred.views.detail', args=(self.data.tagcred.id,)))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['cred'].id, self.data.tagcred.id)
        self.assertNotEqual(resp.context['credlogs'], None)

    def test_detail_nobody(self):
        resp = self.data.nobody.get(reverse('cred.views.detail', args=(self.data.cred.id,)))
        self.assertEqual(resp.status_code, 404)
        resp = self.data.nobody.get(reverse('cred.views.detail', args=(self.data.tagcred.id,)))
        self.assertEqual(resp.status_code, 404)

    def test_add_normal(self):
        resp = self.data.norm.get(reverse('cred.views.add'))
        self.assertEqual(resp.status_code, 200)
        form = resp.context['form']
        self.assertTrue(not form.is_valid())
        resp = self.data.norm.post(reverse('cred.views.add'), {
            'title': 'New Credential',
            'password': 'A password',
            'group': self.data.group.id,
            'iconname': form['iconname'].value(),
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        newcred = Cred.objects.get(title='New Credential')
        self.assertEqual(newcred.password, 'A password')

    def test_edit_normal(self):
        resp = self.data.norm.get(reverse('cred.views.edit', args=(self.data.cred.id,)))
        self.assertEqual(resp.status_code, 200)
        form = resp.context['form']
        post = {}
        for i in form:
            if i.value() is not None:
                post[i.name] = i.value()
        post['title'] = 'New Title'
        del post['attachment']
        resp = self.data.norm.post(reverse('cred.views.edit', args=(self.data.cred.id,)), post, follow=True)
        self.assertEqual(resp.status_code, 200)
        newcred = Cred.objects.get(id=self.data.cred.id)
        self.assertEqual(newcred.title, 'New Title')

    def test_edit_nobody(self):
        resp = self.data.nobody.get(reverse('cred.views.edit', args=(self.data.cred.id,)))
        self.assertEqual(resp.status_code, 404)

    def test_delete_norm(self):
        resp = self.data.norm.get(reverse('cred.views.delete', args=(self.data.cred.id,)))
        self.assertEqual(resp.status_code, 200)
        resp = self.data.norm.post(reverse('cred.views.delete', args=(self.data.cred.id,)))
        delcred = Cred.objects.get(id=self.data.cred.id)
        self.assertTrue(delcred.is_deleted)

    def test_delete_staff(self):
        resp = self.data.staff.get(reverse('cred.views.delete', args=(self.data.cred.id,)))
        self.assertEqual(resp.status_code, 200)
        resp = self.data.staff.post(reverse('cred.views.delete', args=(self.data.cred.id,)), follow=True)
        self.assertEqual(resp.status_code, 200)
        delcred = Cred.objects.get(id=self.data.cred.id)
        self.assertTrue(delcred.is_deleted)

    def test_delete_nobody(self):
        resp = self.data.nobody.get(reverse('cred.views.delete', args=(self.data.cred.id,)))
        self.assertEqual(resp.status_code, 404)
        resp = self.data.nobody.post(reverse('cred.views.delete', args=(self.data.cred.id,)), follow=True)
        self.assertEqual(resp.status_code, 404)
        delcred = Cred.objects.get(id=self.data.cred.id)
        self.assertFalse(delcred.is_deleted)

    def test_tagadd_normal(self):
        resp = self.data.norm.get(reverse('cred.views.tagadd'))
        self.assertEqual(resp.status_code, 200)
        form = resp.context['form']
        post = {}
        for i in form:
            if i.value() is not None:
                post[i.name] = i.value()
        post['name'] = 'New Tag'
        resp = self.data.norm.post(reverse('cred.views.tagadd'), post, follow=True)
        self.assertEqual(resp.status_code, 200)
        newtag = Tag.objects.get(name='New Tag')
        self.assertTrue(newtag is not None)

    def test_tagedit_normal(self):
        resp = self.data.norm.get(reverse('cred.views.tagedit', args=(self.data.tag.id,)))
        self.assertEqual(resp.status_code, 200)
        form = resp.context['form']
        post = {}
        for i in form:
            if i.value() is not None:
                post[i.name] = i.value()
        post['name'] = 'A Tag'
        resp = self.data.norm.post(reverse('cred.views.tagedit', args=(self.data.tag.id,)), post, follow=True)
        self.assertEqual(resp.status_code, 200)
        newtag = Tag.objects.get(name='A Tag')
        self.assertEqual(newtag.id, self.data.tag.id)

    def test_tagdelete_normal(self):
        resp = self.data.norm.get(reverse('cred.views.tagdelete', args=(self.data.tag.id,)))
        self.assertEqual(resp.status_code, 200)
        resp = self.data.staff.post(reverse('cred.views.tagdelete', args=(self.data.tag.id,)), follow=True)
        self.assertEqual(resp.status_code, 200)
        with self.assertRaises(Tag.DoesNotExist):
            Tag.objects.get(id=self.data.tag.id)

    def test_viewqueue_normal(self):
        resp = self.data.norm.get(reverse('cred.views.list', args=('special', 'changeq')))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['credlist']), 1)
        self.assertEqual(resp.context['credlist'][0].id, self.data.cred.id)

    def test_viewqueue_nobody(self):
        resp = self.data.nobody.get(reverse('cred.views.list', args=('special', 'changeq')))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['credlist']), 0)

    def test_addtoqueuestaff(self):
        resp = self.data.staff.get(reverse('cred.views.addtoqueue',
            args=(self.data.tagcred.id,)), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(self.data.tagcred.on_changeq())

    def test_bulkdelete_staff(self):
        resp = self.data.staff.post(reverse('cred.views.bulkdelete'), {'credcheck': self.data.cred.id}, follow=True)
        self.assertEqual(resp.status_code, 200)
        delcred = Cred.objects.get(id=self.data.cred.id)
        self.assertTrue(delcred.is_deleted)

        resp = self.data.staff.post(reverse('cred.views.bulkdelete'), {'credcheck': self.data.cred.id}, follow=True)
        self.assertEqual(resp.status_code, 200)
        with self.assertRaises(Cred.DoesNotExist):
            Cred.objects.get(id=self.data.cred.id)

    def test_bulkaddtochangeq_staff(self):
        resp = self.data.staff.post(reverse('cred.views.bulkaddtoqueue'), {'credcheck': self.data.tagcred.id}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(self.data.tagcred.on_changeq())

    def test_deeplink_post_login_redirect(self):
        testuser = Client()
        loginurl = reverse('login')
        credurl = reverse('cred.views.detail', args=(self.data.cred.id,))
        fullurl = loginurl + '?next=' + credurl
        resp = testuser.post(fullurl, {
            'auth-username': self.data.unorm.username,
            'auth-password': self.data.normpass,
            'rattic_tfa_login_view-current_step': 'auth',
        }, follow=True)
        self.assertRedirects(resp, credurl, status_code=302, target_status_code=200)

    def test_invalid_icon(self):
        resp = self.data.norm.get(reverse('cred.views.list'))
        fakename = 'Namethatdoesnotexist.png'
        self.data.cred.iconname = fakename
        self.data.cred.save()
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, fakename, 200)


CredViewTests = override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))(CredViewTests)
