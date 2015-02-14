from django.test import TestCase
from django.contrib.auth.models import User
from django.core.management import call_command


class AccountCommandTests(TestCase):
    def test_command_demosetup(self):
        args=[]
        opts={}
        call_command('demosetup', *args, **opts)
        u = User.objects.get(username='admin')
        self.assertTrue(u.check_password('rattic'))
        self.assertTrue(u.is_staff)
