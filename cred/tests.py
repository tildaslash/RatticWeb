"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase, Client
from models import Cred
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse

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

class CredHistoryTest(TestCase):
    def setUp(self):
        ourgroup = Group(name='testgroup')
        ourgroup.save()

        self.unorm = User(username='norm', email='norm@example.com')
        self.unorm.set_password('password')
        self.unorm.save()
        self.unorm.groups.add(ourgroup)
        self.unorm.save()

        self.ustaff = User(username='staff', email='steph@example.com')
        self.ustaff.set_password('password')
        self.ustaff.save()

        self.norm = Client()
        self.norm.login(username='norm', password='password')
        self.staff = Client()
        self.staff.login(username='staff', password='password')

        self.cred = Cred(title='secret', password='s3cr3t', group=ourgroup)
        self.cred.save()

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

