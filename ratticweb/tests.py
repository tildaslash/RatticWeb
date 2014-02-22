from django.test import TestCase
from user_sessions.utils.tests import Client
from django.conf import settings
from django.core.urlresolvers import reverse

from django.contrib.auth.models import User, Group
from cred.models import Tag, Cred, CredChangeQ, CredAudit


class TestData:
    def __init__(self):
        if settings.LDAP_ENABLED:
            self.getLDAPAuthData()
        else:
            self.setUpAuthData()
        self.setUpBasicData()

    def login(self, username, password):
        c = Client()
        loginurl = reverse('django.contrib.auth.views.login')
        c.post(loginurl, {'username': username, 'password': password})

        return c

    def getLDAPAuthData(self):
        self.norm = self.login(username='norm', password='password')
        self.unorm = User.objects.get(username='norm')
        self.normpass = 'password'

        self.staff = self.login(username='staff', password='password')
        self.ustaff = User.objects.get(username='staff')

        self.nobody = self.login(username='nobody', password='password')
        self.unobody = User.objects.get(username='nobody')

        self.group = Group.objects.get(name='testgroup')
        self.othergroup = Group.objects.get(name='othergroup')

    def setUpAuthData(self):
        self.group = Group(name='testgroup')
        self.group.save()

        self.othergroup = Group(name='othergroup')
        self.othergroup.save()

        self.unorm = User(username='norm', email='norm@example.com')
        self.unorm.set_password('password')
        self.normpass = 'password'
        self.unorm.save()
        self.unorm.groups.add(self.group)
        self.unorm.save()

        self.ustaff = User(username='staff', email='steph@example.com', is_staff=True)
        self.ustaff.set_password('password')
        self.ustaff.save()
        self.ustaff.groups.add(self.othergroup)
        self.ustaff.save()

        self.unobody = User(username='nobody', email='nobody@example.com')
        self.unobody.set_password('password')
        self.unobody.save()

        self.norm = self.login(username='norm', password='password')
        self.staff = self.login(username='staff', password='password')
        self.nobody = self.login(username='nobody', password='password')

    def setUpBasicData(self):
        self.tag = Tag(name='tag')
        self.tag.save()

        self.cred = Cred(title='secret', username='peh!', password='s3cr3t', group=self.group)
        self.cred.save()
        self.tagcred = Cred(title='tagged', password='t4gg3d', group=self.group)
        self.tagcred.save()
        self.tagcred.tags.add(self.tag)
        self.tagcred.save()
        self.injectcred = Cred(
            title='<script>document.write("BADTITLE!")</script>Bold!',
            username='<script>document.write("BADUNAME!")</script>Italics!',
            password='<script>document.write("BADPWD!")</script>Test',
            group=self.group
        )
        self.injectcred.save()
        self.markdowncred = Cred(title='Markdown Cred', password='qwerty', group=self.group, description='# Test', descriptionmarkdown=True)
        self.markdowncred.save()

        CredChangeQ.objects.add_to_changeq(self.cred)

        self.viewedcred = Cred(title='Viewed', password='s3cr3t', group=self.group)
        self.viewedcred.save()
        self.changedcred = Cred(title='Changed', password='t4gg3d', group=self.group)
        self.changedcred.save()

        CredAudit(audittype=CredAudit.CREDADD, cred=self.viewedcred, user=self.unobody).save()
        CredAudit(audittype=CredAudit.CREDADD, cred=self.changedcred, user=self.unobody).save()
        CredAudit(audittype=CredAudit.CREDVIEW, cred=self.viewedcred, user=self.unorm).save()
        CredAudit(audittype=CredAudit.CREDVIEW, cred=self.changedcred, user=self.unorm).save()
        CredAudit(audittype=CredAudit.CREDCHANGE, cred=self.changedcred, user=self.ustaff).save()

        self.logadd = CredAudit(audittype=CredAudit.CREDADD, cred=self.cred, user=self.ustaff)
        self.logview = CredAudit(audittype=CredAudit.CREDVIEW, cred=self.cred, user=self.ustaff)
        self.logadd.save()
        self.logview.save()


class HomepageTest(TestCase):
    def test_homepage_to_login_redirect(self):
        client = Client()
        response = client.get(reverse('home'), follow=True)
        self.assertTrue(response.redirect_chain[0][0].endswith(reverse('django.contrib.auth.views.login')))
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.status_code, 200)

    def test_admin_disabled(self):
        client = Client()
        response = client.get('/admin/')
        self.assertEqual(response.status_code, 404)
