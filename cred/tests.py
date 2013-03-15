"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from models import Cred
from django.contrib.auth.models import User, Group

class SimpleTest(TestCase):
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


