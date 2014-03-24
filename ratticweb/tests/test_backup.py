from django.test.utils import override_settings
from django.test import TestCase

from django.core.management.base import CommandError
from django.core.management import call_command

from ratticweb.management.commands.backup import BackupStorage, Command as BackupCommand
from ratticweb.tests.helper import a_temp_directory
from db_backup.errors import FailedBackup

import shutil
import uuid
import mock


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
            backup_storage_obj.move_from.assert_called_once_with(destination, backup_dir)
