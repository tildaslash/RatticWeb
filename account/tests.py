from django.test import TestCase, LiveServerTestCase, Client
from django.test.utils import override_settings
from django.utils.unittest import skipIf
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core.management import call_command
from django.conf import settings
from tastypie.models import ApiKey

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait


class AccountViewTests(TestCase):
    username = 'testinguser'
    password = 'testpass'
    testtags = 7
    testitems = 43

    def setUp(self):
        self.client = Client()
        self.u = User(username=self.username, email='you@example.com')
        self.u.set_password(self.password)
        self.u.save()
        profile = self.u.profile
        profile.items_per_page = self.testitems
        profile.save()
        self.client.login(username=self.username, password=self.password)
        # View the profile page to create an API key
        self.client.get(reverse('account.views.profile'))

    def test_profile_page(self):
        response = self.client.get(reverse('account.views.profile'))
        self.assertEqual(response.status_code, 200)
        user = response.context['user']
        self.assertEqual(user.profile.items_per_page, self.testitems)

    def test_newapikey_page(self):
        old = ApiKey.objects.get(user=self.u)
        response = self.client.get(reverse('account.views.newapikey'), follow=True)
        self.assertEqual(response.status_code, 200)
        new = ApiKey.objects.get(user=self.u)
        self.assertNotEqual(old.key, new.key)

    @skipIf(settings.LDAP_ENABLED, 'Test does not apply on LDAP')
    def test_disable_during_login(self):
        response = self.client.get(reverse('account.views.profile'))
        self.assertEqual(response.status_code, 200)
        self.u.is_active=False
        self.u.save()
        response = self.client.get(reverse('account.views.profile'))
        self.assertNotEqual(response.status_code, 200)


class AccountCommandTests(TestCase):
    def test_command_demosetup(self):
        args=[]
        opts={}
        call_command('demosetup', *args, **opts)
        u = User.objects.get(username='admin')
        self.assertTrue(u.check_password('rattic'))
        self.assertTrue(u.is_staff)


class JavascriptTests(LiveServerTestCase):
    def setUp(self):
        self.unorm = User(username='norm', email='norm@example.com')
        self.unorm.set_password('password')
        self.normpass = 'password'
        self.unorm.save()

    @classmethod
    def setUpClass(cls):
        cls.selenium = WebDriver()
        super(JavascriptTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(JavascriptTests, cls).tearDownClass()

    def waitforload(self):
        timeout = 2
        WebDriverWait(self.selenium, timeout).until(
            lambda driver: driver.find_element_by_tag_name('body'))

    def test_login(self):
        self.selenium.get('%s%s' % (self.live_server_url, '/'))
        self.waitforload()
        username_input = self.selenium.find_element_by_name("username")
        username_input.send_keys(self.unorm.username)
        password_input = self.selenium.find_element_by_name("password")
        password_input.send_keys(self.normpass)
        self.selenium.find_element_by_xpath('//input[@value="login"]').click()
        self.assertEquals(self.selenium.current_url, '%s%s' % (self.live_server_url, reverse('cred.views.list')))
        self.waitforload()

    def test_login_wrongpass(self):
        self.selenium.get('%s%s' % (self.live_server_url, '/'))
        self.waitforload()
        username_input = self.selenium.find_element_by_name("username")
        username_input.send_keys(self.unorm.username)
        password_input = self.selenium.find_element_by_name("password")
        password_input.send_keys(self.normpass + 'wrongpass')
        self.selenium.find_element_by_xpath('//input[@value="login"]').click()
        self.assertEquals(self.selenium.current_url, '%s%s' % (self.live_server_url, reverse('django.contrib.auth.views.login')))
        self.waitforload()
        self.selenium.find_element_by_id('loginfailed')

    @skipIf(settings.LDAP_ENABLED, 'Test does not apply on LDAP')
    def test_login_disabled(self):
        self.unorm.is_active = False
        self.unorm.save()
        self.selenium.get('%s%s' % (self.live_server_url, '/'))
        self.waitforload()
        username_input = self.selenium.find_element_by_name("username")
        username_input.send_keys(self.unorm.username)
        password_input = self.selenium.find_element_by_name("password")
        password_input.send_keys(self.normpass)
        self.selenium.find_element_by_xpath('//input[@value="login"]').click()
        self.assertEquals(self.selenium.current_url, '%s%s' % (self.live_server_url, reverse('django.contrib.auth.views.login')))
        self.waitforload()
        self.selenium.find_element_by_id('loginfailed')


JavascriptTests = override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))(JavascriptTests)
