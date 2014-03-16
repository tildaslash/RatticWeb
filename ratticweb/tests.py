from django.test import TestCase
from django.test.utils import override_settings
from user_sessions.utils.tests import Client
from django.conf import settings
from django.core.urlresolvers import reverse

from django.core.management import call_command
from django.contrib.auth.models import User, Group
from django.core.management.base import CommandError
from cred.models import Tag, Cred, CredChangeQ, CredAudit

from ratticweb.management.commands.backup import BackupStorage, Command as BackupCommand
from ratticweb.management.commands.restore import Command as RestoreCommand
from db_backup.errors import FailedBackup

from contextlib import contextmanager
from moto import mock_s3
import tempfile
import logging
import shutil
import uuid
import mock
import boto
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
def a_temp_file(contents=None):
    """Yield us a temporary file to play with"""
    fle = None
    try:
        fle = tempfile.NamedTemporaryFile(delete=False).name
        if contents:
            with open(fle, "w") as the_file:
                the_file.write(contents)
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

    @mock.patch("ratticweb.management.commands.backup.BackupStorage")
    @mock.patch("ratticweb.management.commands.backup.Command.validate_options")
    @mock.patch("ratticweb.management.commands.backup.backup")
    def test_it_validates_options(self, fake_backup, fake_validate_options, FakeBackupStorage):
        backup_dir = mock.Mock(name="backup_dir")
        recipients = mock.Mock(name="recipients")
        FakeBackupStorage.return_value = mock.MagicMock(spec=BackupStorage)
        with override_settings(BACKUP_DIR=backup_dir, BACKUP_RECIPIENTS=recipients):
            call_command("backup")
            fake_validate_options.assert_called_once_with(backup_dir, recipients)

    @mock.patch("ratticweb.management.commands.backup.BackupStorage")
    @mock.patch("ratticweb.management.commands.backup.Command.validate_options")
    @mock.patch("ratticweb.management.commands.backup.backup")
    def test_it_calls_backup(self, fake_backup, fake_validate_options, FakeBackupStorage):
        gpg_home = mock.Mock(name="gpg_home")
        backup_dir = mock.Mock(name="backup_dir")
        recipients = mock.Mock(name="recipients")
        default_db = mock.Mock(name="default_db")
        FakeBackupStorage.return_value = mock.MagicMock(spec=BackupStorage)
        with override_settings(BACKUP_DIR=backup_dir, BACKUP_RECIPIENTS=recipients, DATABASES={'default': default_db}, BACKUP_GPG_HOME=gpg_home):
            call_command("backup")
            fake_validate_options.assert_called_once_with(backup_dir, recipients)
            fake_backup.assert_called_once_with(default_db, recipients, backup_dir, gpg_home=gpg_home)

    @mock.patch("ratticweb.management.commands.backup.BackupStorage")
    @mock.patch("ratticweb.management.commands.backup.Command.validate_options")
    @mock.patch("ratticweb.management.commands.backup.backup")
    def test_it_splits_recipients_by_comma_if_a_string(self, fake_backup, fake_validate_options, FakeBackupStorage):
        backup_dir = mock.Mock(name="backup_dir")
        recipients = "things,and,stuff"
        default_db = mock.Mock(name="default_db")
        FakeBackupStorage.return_value = mock.MagicMock(spec=BackupStorage)
        with override_settings(BACKUP_DIR=backup_dir, BACKUP_RECIPIENTS=recipients, DATABASES={'default': default_db}):
            call_command("backup")
            fake_validate_options.assert_called_once_with(backup_dir, recipients)
            fake_backup.assert_called_once_with(default_db, ["things", "and", "stuff"], backup_dir, gpg_home=None)

    @mock.patch("ratticweb.management.commands.backup.BackupStorage")
    @mock.patch("ratticweb.management.commands.backup.Command.validate_options")
    @mock.patch("ratticweb.management.commands.backup.backup")
    def test_it_converts_FailedBackup_errors_to_CommandError(self, fake_backup, fake_validate_options, FakeBackupStorage):
        backup_dir = mock.Mock(name="backup_dir")
        recipients = mock.Mock(name="recipients")
        default_db = mock.Mock(name="default_db")
        backup_storage = mock.MagicMock(spec=BackupStorage)

        error_message = str(uuid.uuid1())
        error = FailedBackup(error_message)
        fake_backup.side_effect = error

        error_message2 = str(uuid.uuid1())
        error2 = FailedBackup(error_message2)
        FakeBackupStorage.return_value = backup_storage

        with override_settings(BACKUP_DIR=backup_dir, BACKUP_RECIPIENTS=recipients, DATABASES={'default': default_db}):
            # call_command results in the CommandError being caught and propagated as SystemExit

            with self.assertRaisesRegexp(CommandError, error_message):
                self.command.handle()

            # And make sure it catches exceptions from the storage context manager
            backup_storage.__enter__.side_effect = error2
            with self.assertRaisesRegexp(CommandError, error_message2):
                self.command.handle()

    @mock.patch("ratticweb.management.commands.backup.BackupStorage")
    @mock.patch("ratticweb.management.commands.backup.Command.validate_options")
    @mock.patch("ratticweb.management.commands.backup.backup")
    def test_it_sends_backup_to_storage(self, fake_backup, fake_validate_options, FakeBackupStorage):
        default_db = mock.Mock(name="default_db")
        recipients = mock.Mock(name="recipients")
        backup_dir = mock.Mock(name="backup_dir")

        backup_storage = mock.MagicMock(spec=BackupStorage)
        backup_storage_obj = mock.Mock(name="backup_storage")
        backup_storage.__enter__ = mock.Mock(return_value=backup_storage_obj)
        FakeBackupStorage.return_value = backup_storage

        destination = mock.Mock(name="destination")
        fake_backup.return_value = destination

        with override_settings(BACKUP_DIR=backup_dir, BACKUP_RECIPIENTS=recipients, DATABASES={'default': default_db}):
            call_command("backup")
            backup_storage_obj.send_from.assert_called_once_with(destination, backup_dir)


class RestoreManagementCommandTest(TestCase):
    def setUp(self):
        self.command = RestoreCommand()

    def test_complains_if_no_restore_from_specified(self):
        with self.assertRaisesRegexp(CommandError, "Please specify --restore-from.+"):
            self.command.handle(restore_from=None)

    def test_complains_if_restore_from_doesnt_exist(self):
        with a_temp_file() as restore_from:
            if os.path.exists(restore_from):
                os.remove(restore_from)

            with self.assertRaisesRegexp(CommandError, "Specified backup file \({0}\) doesn't exist".format(restore_from)):
                self.command.handle(restore_from=restore_from)

    @mock.patch("os.path.exists")
    @mock.patch("ratticweb.management.commands.restore.restore")
    def test_calls_restore(self, fake_restore, fake_exists):
        gpg_home = mock.Mock(name="gpg_home")
        default_db = mock.Mock(name="default_db")
        restore_from = mock.Mock(name="restore_from")

        fake_exists.side_effect = lambda p: True

        with override_settings(DATABASES={'default': default_db}, BACKUP_GPG_HOME=gpg_home):
            call_command("restore", restore_from=restore_from)
            fake_restore.assert_called_once_with(default_db, restore_from, gpg_home=gpg_home)
            fake_exists.assert_called_once_with(restore_from)

    @mock.patch("os.path.exists")
    @mock.patch("ratticweb.management.commands.restore.restore")
    def test_converts_FailedBackup_errors_into_CommandError(self, fake_restore, fake_exists):
        default_db = mock.Mock(name="default_db")
        restore_from = mock.Mock(name="restore_from")
        fake_exists.side_effect = lambda p: True

        error_message = str(uuid.uuid1())
        error = FailedBackup(error_message)
        fake_restore.side_effect = error

        with override_settings(DATABASES={'default': default_db}):
            with self.assertRaisesRegexp(CommandError, error_message):
                # call_command results in the CommandError being caught and propagated as SystemExit
                self.command.handle(restore_from=restore_from)
            fake_exists.assert_called_once_with(restore_from)


class BackupStorageTest(TestCase):
    def setUp(self):
        self.storage = BackupStorage()

        # Only want the logs to show if the tests fail
        logging.getLogger("db_backup").handlers = []

    def test_says_no_storage_after_initialization(self):
        self.assertIs(self.storage.bucket, None)
        self.assertIs(self.storage.has_storage, False)
        self.assertIs(self.storage.bucket_location, None)

    def test_validates_on_enter(self):
        validate_destination = mock.Mock(name="validate_destination")
        with mock.patch.object(self.storage, "validate_destination", validate_destination):
            with self.storage as storage:
                self.assertIs(storage, self.storage)
                self.storage.validate_destination.assert_called_once()

    @mock.patch("ratticweb.management.commands.storage.S3Connection")
    def test_doesnt_connect_to_s3_if_no_BACKUP_S3_BUCKET_setting(self, FakeS3Connection):
        with override_settings(BACKUP_S3_BUCKET=None):
            self.storage.validate_destination()
        FakeS3Connection.assert_not_called()

    @mock_s3
    def test_complains_if_no_bucket(self):
        with self.assertRaisesRegexp(FailedBackup, "Please first create the s3 bucket.+"):
            with override_settings(BACKUP_S3_BUCKET="bucket_location"):
                self.storage.validate_destination()

        self.assertIs(self.storage.has_storage, False)

    @mock.patch("ratticweb.management.commands.storage.S3Connection")
    def test_complains_if_forbidden_bucket(self, FakeS3Connection):
        error = boto.exception.S3ResponseError(403, "Forbidden")
        conn = mock.Mock(name="connection")
        conn.get_bucket.side_effect = error
        FakeS3Connection.return_value = conn

        with self.assertRaises(boto.exception.S3ResponseError):
            with override_settings(BACKUP_S3_BUCKET="blah"):
                self.storage.validate_destination()

        conn.get_bucket.assert_called_once_with("blah")
        self.assertIs(self.storage.has_storage, False)

    @mock_s3
    def test_sets_has_storage_if_successfully_finds_bucket(self):
        bucket_name = str(uuid.uuid1())
        conn = boto.connect_s3()
        conn.create_bucket(bucket_name)

        with override_settings(BACKUP_S3_BUCKET=bucket_name):
            self.storage.validate_destination()

        self.assertIs(self.storage.has_storage, True)
        self.assertIs(self.storage.bucket_location, bucket_name)
        self.assertIs(type(self.storage.bucket), boto.s3.bucket.Bucket)

    def test_send_from_does_nothing_if_no_has_storage(self):
        upload_to_s3 = mock.Mock(name="upload_to_s3")
        self.assertIs(self.storage.has_storage, False)
        with mock.patch.object(self.storage, "upload_to_s3", upload_to_s3):
            self.storage.send_from("/one/two/three.gpg", "/one/")
            self.storage.upload_to_s3.assert_not_called()

    @mock_s3
    def test_send_from_does_send_to_s3_if_has_storage(self):
        contents = """
        Stuff and things
        blah
        """

        bucket_name = str(uuid.uuid1())
        conn = boto.connect_s3()
        conn.create_bucket(bucket_name)

        with a_temp_file(contents) as source:
            with override_settings(BACKUP_S3_BUCKET=bucket_name):
                self.storage.validate_destination()
                self.storage.send_from(source, os.path.dirname(source))

            self.assertEqual(boto.connect_s3().get_bucket(bucket_name).get_key(os.path.basename(source)).get_contents_as_string(), contents)
