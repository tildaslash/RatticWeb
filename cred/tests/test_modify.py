from django.test import TestCase
from django.contrib.auth.models import Group

from cred.models import Cred


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
