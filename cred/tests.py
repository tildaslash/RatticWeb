from django.utils import unittest

from django.test import TestCase, Client, LiveServerTestCase
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.conf import settings

from models import Cred, Tag
from ratticweb.tests import TestData

from cred.icon import get_icon_data

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.firefox.webdriver import FirefoxProfile
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys


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
        self.data = TestData()

    def test_list_normal(self):
        resp = self.data.norm.get(reverse('cred.views.list'))
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

    def test_deeplink_login_redirect(self):
        testuser = Client()
        loginurl = reverse('django.contrib.auth.views.login')
        credurl = reverse('cred.views.detail', args=(self.data.cred.id,))
        nexturl = loginurl + '?next=' + credurl
        resp = testuser.get(credurl, follow=True)
        self.assertRedirects(resp, nexturl, status_code=302, target_status_code=200)
        self.assertEqual(resp.context['next'], credurl)

    def test_deeplink_post_login_redirect(self):
        testuser = Client()
        loginurl = reverse('django.contrib.auth.views.login')
        credurl = reverse('cred.views.detail', args=(self.data.cred.id,))
        fullurl = loginurl + '?next=' + credurl
        resp = testuser.post(fullurl, {'username': self.data.unorm.username, 'password': self.data.normpass}, follow=True)
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
        self.selenium.get('%s%s' % (self.live_server_url, '/'))
        self.waitforload()
        username_input = self.selenium.find_element_by_name("username")
        username_input.send_keys(username)
        password_input = self.selenium.find_element_by_name("password")
        password_input.send_keys(password)
        self.selenium.find_element_by_xpath('//input[@value="login"]').click()
        self.waitforload()

    def test_search(self):
        self.login_as(self.data.unorm.username, self.data.normpass)
        self.selenium.get('%s%s' % (self.live_server_url, reverse('cred.views.list')))
        self.waitforload()
        searchbox = self.selenium.find_element_by_id("search-box")
        searchbox.send_keys("secret")
        searchbox.send_keys(Keys.ENTER)
        self.waitforload()
        self.assertEquals(self.selenium.current_url, '%s%s' % (self.live_server_url, reverse('cred.views.list', args=('search', 'secret'))))

    @unittest.expectedFailure
    def test_password_details(self):
        timeout = 4
        self.login_as(self.data.unorm.username, self.data.normpass)
        self.selenium.get('%s%s' % (self.live_server_url,
            reverse('cred.views.detail', args=(self.data.cred.id,))))
        self.waitforload()
        elempass = self.selenium.find_element_by_id('password')
        # Check password is hidden
        self.assertTrue('passhidden' in elempass.get_attribute('class'))
        # Check password isn't correct
        self.assertNotEquals(elempass.text, self.data.cred.password)
        # Hover over password
        hov = ActionChains(self.selenium).move_to_element(elempass)
        hov.perform()
        # Check password is fetched
        WebDriverWait(self.selenium, timeout).until(
            lambda driver: driver.find_element_by_id('password').text == self.data.cred.password)
        # Check password is still hidden
        self.assertTrue('passhidden' in elempass.get_attribute('class'))
        # Click show button
        self.selenium.find_element_by_id('showpass').click()
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
        # Check password
        self.assertEqual(currpass, self.data.cred.password)
        # Check password is hidden
        WebDriverWait(self.selenium, timeout).until(
            lambda driver: driver.find_element_by_id('id_password').get_attribute('type') == 'password')
        # Click show button
        self.selenium.find_element_by_id('passtoggle').click()
        # Check password is visible
        WebDriverWait(self.selenium, timeout).until(
            lambda driver: driver.find_element_by_id('id_password').get_attribute('type') == 'text')
        # Click hide button
        self.selenium.find_element_by_id('passtoggle').click()
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
        # Check Logo
        self.assertEqual(currlogo, self.data.cred.iconname)
        # Click change logo button
        self.selenium.find_element_by_id('choosebutton').click()
        # Wait for dialog
        WebDriverWait(self.selenium, timeout).until(
            lambda driver: driver.find_element_by_id('logomodalimg_3').is_displayed())
        # Pick the third logo
        self.selenium.find_element_by_id('logomodalimg_3').click()
        # Wait for dialog to go
        WebDriverWait(self.selenium, timeout).until(
            lambda driver: not driver.find_element_by_id('logomodalimg_3').is_displayed())
        # Check the new iconname is in the list
        iconname = self.selenium.find_element_by_id('id_iconname').get_attribute('value')
        icondata = get_icon_data()[iconname]
        # Validate the logo is shown correctly
        logodisplay = self.selenium.find_element_by_id('logodisplay')
        logocss = logodisplay.get_attribute('style')
        spritelocation = settings.STATIC_URL + settings.CRED_ICON_SPRITE
        self.assertRegexpMatches(logocss, r'width:\W+' + str(icondata['width']) + r'px;')
        self.assertRegexpMatches(logocss, r'height:\W+' + str(icondata['height']) + r'px;')
        self.assertRegexpMatches(logocss, r'background:\W+url\("' + spritelocation + r'"\)\W+repeat\W+scroll\W+-?'
                                          + str(icondata['xoffset']) + r'px\W+-?' + str(icondata['yoffset']) + r'px\W+transparent;')
        # Save the credential
        self.selenium.find_element_by_id('credsave').click()
        self.waitforload()
        # Check it has the right data now
        chgcred = Cred.objects.get(id=self.data.cred.id)
        self.assertEqual(chgcred.iconname, iconname)

    @unittest.expectedFailure
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
        self.selenium.find_element_by_id('showpass').click()
        # Check password is fetched
        WebDriverWait(self.selenium, timeout).until(
            lambda driver: driver.find_element_by_id('password').text == self.data.injectcred.password)
        # Check password is visible
        self.assertTrue('passhidden' not in elempass.get_attribute('class'))


CredViewTests = override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))(CredViewTests)
JavascriptTests = override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))(JavascriptTests)
