from django.test import LiveServerTestCase
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.utils.unittest import SkipTest

from cred.models import Cred
from ratticweb.tests.helper import TestData

from cred.icon import get_icon_data

from url_decode import urldecode
import random
import time

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.firefox.webdriver import FirefoxProfile
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys

from testconfig import config


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


JavascriptTests = override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))(JavascriptTests)
