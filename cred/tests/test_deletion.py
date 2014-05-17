from django.test import TestCase
from django.contrib.auth.models import Group

from cred.models import Cred


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
