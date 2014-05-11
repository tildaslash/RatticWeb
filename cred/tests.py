from django.test import TestCase, Client, LiveServerTestCase
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.core import mail
from django.conf import settings
from django.test.utils import override_settings
from django.utils.unittest import SkipTest

from models import Cred, Tag
from ratticweb.tests.helper import TestData

from cred.icon import get_icon_data
from cred.tasks import change_queue_emails

from url_decode import urldecode
import random
import time

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.firefox.webdriver import FirefoxProfile
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys

from testconfig import config


class CredAccessTest(TestCase):
    def setUp(self):
        g = Group(name='h')
        g.save()

        c = Cred(title='testcred', password='1234', group=g)
        c.save()

        d = Cred(title='todelete', password='12345678', group=g)
        d.save()
        d.delete()

        md = Cred(title='Markdown Cred', password='qwerty', group=g, description='# Test')
        md.save()

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
        self.assertTrue(self.c.is_accessible_by(self.u))
        self.assertTrue(not self.c.is_accessible_by(self.f))

    def test_credlist_visible(self):
        self.assertTrue(self.c in Cred.objects.accessible(self.u))
        self.assertTrue(self.c not in Cred.objects.accessible(self.f))

    def test_deleted_access(self):
        self.assertTrue(self.d.is_accessible_by(self.s))
        self.assertTrue(not self.d.is_accessible_by(self.u))

    def test_deleted_visibility(self):
        self.assertTrue(self.d in Cred.objects.accessible(self.s, deleted=True))
        self.assertTrue(self.d not in Cred.objects.accessible(self.u, deleted=True))


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


class CredAttachmentTest(TestCase):
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

        # Open a test file and upload it
        with open('docs/keepass/test2.kdb', 'r') as fp:
            post['attachment'] = fp

            resp = self.data.norm.post(
                reverse('cred.views.edit', args=(self.data.cred.id, )),
                post
            )
            self.assertEqual(resp.status_code, 302)

        # Get a new copy of the cred from the DB
        cred = Cred.objects.get(pk=self.data.cred.id)

        # Check it matches the test file
        with open('docs/keepass/test2.kdb', 'r') as fp:
            self.assertEqual(fp.read(), cred.attachment.read())


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


class CredModifyTest(TestCase):
    def setUp(self):
        g = Group(name='h')
        g.save()

        c = Cred(title='modifycred', password='1234', group=g)
        c.save()

        self.c = c

    def test_modify_date_metadata_change(self):
        c = self.c

        # Make a metadata change
        oldtime = c.modified
        self.assertIsNotNone(oldtime)
        c.description = 'something here'
        c.save()

        # Check the modified time didn't change
        newtime = c.modified
        self.assertEqual(newtime, oldtime)

    def test_modify_date_cred_change(self):
        c = self.c

        # Make a non-metadata change
        oldtime = c.modified
        self.assertIsNotNone(oldtime)
        c.title = 'something here'
        c.save()

        # Check the modified time didn't change
        newtime = c.modified
        self.assertGreater(newtime, oldtime)


class CredEmailTests(TestCase):
    def setUp(self):
        self.data = TestData()

    def test_change_queue_email(self):
        change_queue_emails()

        print mail.outbox[0].body

        salutation = 'Hello ' + self.data.unorm.username + ',\n'
        credlink = 'https://' + settings.HOSTNAME + reverse('cred.views.detail', args=(self.data.cred.id, ))

        self.assertEqual('RatticDB - Passwords requiring changes', mail.outbox[0].subject)
        self.assertEqual(1, len(mail.outbox[0].to))
        self.assertEqual(self.data.unorm.email, mail.outbox[0].to[0])
        self.assertIn(salutation, mail.outbox[0].body)
        self.assertIn(credlink, mail.outbox[0].body)


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


class JavascriptTests(LiveServerTestCase):
    def setUp(self):
        self.data = TestData()

    @classmethod
    def setUpClass(cls):
        if config.get("no_selenium"):
            raise SkipTest("Told not to run selenium tests")

        ffp = FirefoxProfile()
        ffp.native_events_enabled = True
        cls.selenium = WebDriver(ffp)
        super(JavascriptTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(JavascriptTests, cls).tearDownClass()

    def waitforload(self):
        timeout = 4
        WebDriverWait(self.selenium, timeout).until(
            lambda driver: driver.find_element_by_tag_name('body'))

    def login_as(self, username, password):
        self.selenium.get('%s%s' % (self.live_server_url, reverse('home')))
        self.waitforload()
        username_input = self.selenium.find_element_by_name("auth-username")
        username_input.send_keys(username)
        password_input = self.selenium.find_element_by_name("auth-password")
        password_input.send_keys(password)
        self.selenium.find_element_by_xpath('//input[@value="Login"]').click()
        self.waitforload()

    def test_search(self):
        searchkey = "_secr3t.p@ssw()rd's\\te5t!"
        self.login_as(self.data.unorm.username, self.data.normpass)
        self.selenium.get('%s%s' % (self.live_server_url, reverse('cred.views.list')))
        self.waitforload()
        searchbox = self.selenium.find_element_by_id("search-box")
        searchbox.send_keys(searchkey)
        searchbox.send_keys(Keys.ENTER)
        self.waitforload()
        cur_url = urldecode(self.selenium.current_url)
        plan_url = urldecode('%s%s' % (self.live_server_url, reverse('cred.views.list', args=('search', searchkey))))
        self.assertEquals(cur_url, plan_url)

    def test_password_details(self):
        self.login_as(self.data.unorm.username, self.data.normpass)
        self.selenium.get('%s%s' % (self.live_server_url,
            reverse('cred.views.detail', args=(self.data.cred.id,))))
        self.waitforload()
        elempass = self.selenium.find_element_by_id('password')
        # Check password is hidden
        self.assertTrue('passhidden' in elempass.get_attribute('class'))
        # Check password isn't correct
        self.assertNotEquals(elempass.text, self.data.cred.password)
        # Click show button
        self.selenium.find_elements_by_xpath("//button[contains(concat(' ', @class, ' '), ' btn-pass-fetchcred ')]")[0].click()
        # Check password is visible
        self.assertTrue('passhidden' not in elempass.get_attribute('class'))

    def test_password_edit(self):
        timeout = 4
        self.login_as(self.data.unorm.username, self.data.normpass)
        self.selenium.get('%s%s' % (self.live_server_url,
            reverse('cred.views.edit', args=(self.data.cred.id,))))
        self.waitforload()
        elempass = self.selenium.find_element_by_id('id_password')
        currpass = elempass.get_attribute('value')
        showbutton = self.selenium.find_elements_by_xpath("//button[contains(concat(' ', @class, ' '), ' btn-password-visibility ')]")[0]
        # Check password
        self.assertEqual(currpass, self.data.cred.password)
        # Check password is hidden
        WebDriverWait(self.selenium, timeout).until(
            lambda driver: driver.find_element_by_id('id_password').get_attribute('type') == 'password')
        # Click show button
        showbutton.click()
        # Check password is visible
        WebDriverWait(self.selenium, timeout).until(
            lambda driver: driver.find_element_by_id('id_password').get_attribute('type') == 'text')
        # Click hide button
        showbutton.click()
        # Check password is hidden
        WebDriverWait(self.selenium, timeout).until(
            lambda driver: driver.find_element_by_id('id_password').get_attribute('type') == 'password')

    def test_password_edit_logo(self):
        timeout = 4
        self.login_as(self.data.unorm.username, self.data.normpass)
        self.selenium.get('%s%s' % (self.live_server_url,
            reverse('cred.views.edit', args=(self.data.cred.id,))))
        self.waitforload()
        elemlogo = self.selenium.find_element_by_id('id_iconname')
        currlogo = elemlogo.get_attribute('value')
        otherimg = self.selenium.find_element_by_xpath('.//*[@id=\'logoModal\']/div[2]/div/img[8]')
        # Check Logo
        self.assertEqual(currlogo, self.data.cred.iconname)
        # Click change logo button
        self.selenium.find_element_by_id('choosebutton').click()
        # Wait for dialog
        WebDriverWait(self.selenium, timeout).until(
            lambda driver: otherimg.is_displayed())
        # Pick the third logo
        otherimg.click()
        # Wait for dialog to go
        WebDriverWait(self.selenium, timeout).until(
            lambda driver: not otherimg.is_displayed())
        # Check the new iconname is in the list
        iconname = self.selenium.find_element_by_id('id_iconname').get_attribute('value')
        icondata = get_icon_data()[iconname]
        # Validate the logo is shown correctly
        logodisplay = self.selenium.find_element_by_id('logodisplay')
        logoclasses = logodisplay.get_attribute('class')
        self.assertIn(icondata['css-class'], logoclasses)
        self.assertNotIn('rattic-icon-clickable', logoclasses)
        # Save the credential
        logodisplay.submit()
        self.waitforload()
        # Check it has the right data now
        chgcred = Cred.objects.get(id=self.data.cred.id)
        self.assertEqual(chgcred.iconname, iconname)

    def test_password_generator(self):
        timeout = 4
        self.login_as(self.data.unorm.username, self.data.normpass)
        self.selenium.get('%s%s' % (self.live_server_url,
            reverse('cred.views.edit', args=(self.data.cred.id,))))
        self.waitforload()
        elempass = self.selenium.find_element_by_id('id_password')
        # Check password is hidden
        self.assertEqual(elempass.get_attribute('type'), 'password')
        # Get password
        currpass = elempass.get_attribute('value')
        # Check password
        self.assertEqual(currpass, self.data.cred.password)
        # Show Dialog
        self.selenium.find_element_by_id('genpass').click()
        # Inject some entropy so we can generate randomness on travis-ci
        start = time.time()
        while self.selenium.execute_script("return sjcl.random.isReady()") == 0:
            self.selenium.execute_script("sjcl.random.addEntropy({0}, 1, 'tests')".format(random.randint(0, 30000)))
            if time.time() - start > 10:
                raise Exception("Failed to seed the test!")
        # Wait for dialog
        WebDriverWait(self.selenium, timeout).until(
            lambda driver: driver.find_element_by_id('genpassconfirm').is_displayed())
        # Generate password
        self.selenium.find_element_by_id('genpassconfirm').click()
        # Wait for dialog
        WebDriverWait(self.selenium, timeout).until(
            lambda driver: driver.find_element_by_id('id_password').get_attribute('value') != self.data.cred.password)
        currpass = elempass.get_attribute('value')
        self.assertNotEqual(currpass, self.data.cred.password)
        self.assertEqual(len(currpass), 12)

    def test_script_injection(self):
        timeout = 4
        self.login_as(self.data.unorm.username, self.data.normpass)
        self.selenium.get('%s%s' % (self.live_server_url,
            reverse('cred.views.detail', args=(self.data.injectcred.id,))))
        self.waitforload()
        elempass = self.selenium.find_element_by_id('password')
        # Hover over password
        self.selenium.find_elements_by_xpath("//button[contains(concat(' ', @class, ' '), ' btn-pass-fetchcred ')]")[0].click()
        # Check password is fetched
        WebDriverWait(self.selenium, timeout).until(
            lambda driver: driver.find_element_by_id('password').text == self.data.injectcred.password)
        # Check password is visible
        self.assertTrue('passhidden' not in elempass.get_attribute('class'))


CredViewTests = override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))(CredViewTests)
CredEmailTests = override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))(CredEmailTests)
CredAttachmentTest = override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))(CredAttachmentTest)
JavascriptTests = override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))(JavascriptTests)
