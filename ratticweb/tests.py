from django.test import TestCase
from django.test.utils import override_settings
from user_sessions.utils.tests import Client
from django.conf import settings
from django.core.urlresolvers import reverse

from django.core.management import call_command
from django.contrib.auth.models import User, Group
from django.core.management.base import CommandError
from cred.models import Tag, Cred, CredChangeQ, CredAudit

from ratticweb.management.commands.restore import Command as RestoreCommand
from ratticweb.management.commands.backup import Command as BackupCommand
from db_backup.errors import FailedBackup

from contextlib import contextmanager
import tempfile
import shutil
import uuid
import mock
import os


@contextmanager
def a_temp_directory():
    """Yield us a temporary directory to play with"""
    directory = None
    try:
        directory = tempfile.mkdtemp()
        yield directory
    finally:
        if directory and os.path.exists(directory):
            shutil.rmtree(directory)


@contextmanager
def a_temp_file():
    """Yield us a temporary file to play with"""
    fle = None
    try:
        fle = tempfile.NamedTemporaryFile(delete=False).name
        yield fle
    finally:
        if fle and os.path.exists(fle):
            os.remove(fle)


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


class BackupManagementCommandTest(TestCase):
    def setUp(self):
        self.command = BackupCommand()

    def test_complains_if_backup_dir_is_none(self):
        with self.assertRaisesRegexp(CommandError, "No backup directory has been specified.+"):
            self.command.validate_options(None, [])

    def test_complains_if_backup_dir_doesnt_exist(self):
        with a_temp_directory() as backup_dir:
            shutil.rmtree(backup_dir)
            with self.assertRaisesRegexp(CommandError, "Specified backup_dir \({0}\) doesn't exist".format(backup_dir)):
                self.command.validate_options(backup_dir, [])

    def test_complains_if_no_recipients(self):
        with a_temp_directory() as backup_dir:
            with self.assertRaisesRegexp(CommandError, "No recipients list has been specified.+"):
                self.command.validate_options(backup_dir, None)

    def test_complains_if_recipients_isnt_a_list_or_string(self):
        with a_temp_directory() as backup_dir:
            for recipients in (0, 1, {}, {1: 1}, False, True, lambda: 1):
                with self.assertRaisesRegexp(CommandError, "Recipients list needs to be a list of strings.+"):
                    self.command.validate_options(backup_dir, recipients)

    @mock.patch("ratticweb.management.commands.backup.Command.validate_options")
    @mock.patch("ratticweb.management.commands.backup.backup")
    def test_it_validates_options(self, fake_backup, fake_validate_options):
        backup_dir = mock.Mock(name="backup_dir")
        recipients = mock.Mock(name="recipients")
        with override_settings(BACKUP_DIR=backup_dir, BACKUP_RECIPIENTS=recipients):
            call_command("backup")
            fake_validate_options.assert_called_once_with(backup_dir, recipients)

    @mock.patch("ratticweb.management.commands.backup.Command.validate_options")
    @mock.patch("ratticweb.management.commands.backup.backup")
    def test_it_calls_backup(self, fake_backup, fake_validate_options):
        backup_dir = mock.Mock(name="backup_dir")
        recipients = mock.Mock(name="recipients")
        default_db = mock.Mock(name="default_db")
        with override_settings(BACKUP_DIR=backup_dir, BACKUP_RECIPIENTS=recipients, DATABASES={'default': default_db}):
            call_command("backup")
            fake_validate_options.assert_called_once_with(backup_dir, recipients)
            fake_backup.assert_called_once_with(default_db, recipients, backup_dir)

    @mock.patch("ratticweb.management.commands.backup.Command.validate_options")
    @mock.patch("ratticweb.management.commands.backup.backup")
    def test_it_splits_recipients_by_comma_if_a_string(self, fake_backup, fake_validate_options):
        backup_dir = mock.Mock(name="backup_dir")
        recipients = "things,and,stuff"
        default_db = mock.Mock(name="default_db")
        with override_settings(BACKUP_DIR=backup_dir, BACKUP_RECIPIENTS=recipients, DATABASES={'default': default_db}):
            call_command("backup")
            fake_validate_options.assert_called_once_with(backup_dir, recipients)
            fake_backup.assert_called_once_with(default_db, ["things", "and", "stuff"], backup_dir)

    @mock.patch("ratticweb.management.commands.backup.Command.validate_options")
    @mock.patch("ratticweb.management.commands.backup.backup")
    def test_it_converts_FailedBackup_errors_to_CommandError(self, fake_backup, fake_validate_options):
        backup_dir = mock.Mock(name="backup_dir")
        recipients = mock.Mock(name="recipients")
        default_db = mock.Mock(name="default_db")

        error_message = str(uuid.uuid1())
        error = FailedBackup(error_message)
        fake_backup.side_effect = error

        with override_settings(BACKUP_DIR=backup_dir, BACKUP_RECIPIENTS=recipients, DATABASES={'default': default_db}):
            with self.assertRaisesRegexp(CommandError, error_message):
                # call_command results in the CommandError being caught and propagated as SystemExit
                self.command.handle()


class RestoreManagementCommandTest(TestCase):
    def setUp(self):
        self.command = RestoreCommand()

    def it_complains_if_no_restore_from_specified(self):
        with self.assertRaisesRegexp(CommandError, "Please specify --restore-from.+"):
            self.command.handle(restore_from=None)

    def it_complains_if_restore_from_doesnt_exist(self):
        with a_temp_file() as restore_from:
            with self.assertRaisesRegexp(CommandError, "Specified backup file \({0}\) doesn't exist".format(restore_from)):
                self.command.handle(restore_from=restore_from)

    @mock.patch("ratticweb.management.commands.backup.restore")
    def it_calls_restore(self, fake_restore):
        default_db = mock.Mock(name="default_db")
        restore_from = mock.Mock(name="restore_from")

        with override_settings(DATABASES={'default': default_db}):
            call_command("restore", restore_from=restore_from)
            fake_restore.assert_called_once_with(default_db, restore_from)

    @mock.patch("ratticweb.management.commands.backup.restore")
    def it_converts_FailedBackup_errors_into_CommandError(self, fake_restore):
        default_db = mock.Mock(name="default_db")
        restore_from = mock.Mock(name="restore_from")

        error_message = str(uuid.uuid1())
        error = FailedBackup(error_message)
        fake_restore.side_effect = error

        with override_settings(DATABASES={'default': default_db}):
            with self.assertRaisesRegexp(CommandError, error_message):
                # call_command results in the CommandError being caught and propagated as SystemExit
                self.command.handle(restore_from=restore_from)
