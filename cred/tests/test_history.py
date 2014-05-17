from django.test import TestCase
from django.contrib.auth.models import Group

from cred.models import Cred


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
