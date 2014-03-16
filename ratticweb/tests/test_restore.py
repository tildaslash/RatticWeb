from django.test.utils import override_settings
from django.test import TestCase

from django.core.management.base import CommandError
from django.core.management import call_command

from ratticweb.management.commands.restore import Command as RestoreCommand
from ratticweb.tests.helper import a_temp_file
from db_backup.errors import FailedBackup

import uuid
import mock
import os


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
        restore_from.startswith.return_value = False

        fake_exists.side_effect = lambda p: True

        with override_settings(DATABASES={'default': default_db}, BACKUP_GPG_HOME=gpg_home):
            call_command("restore", restore_from=restore_from)
            fake_restore.assert_called_once_with(default_db, restore_from, gpg_home=gpg_home)
            fake_exists.assert_called_once_with(restore_from)
            restore_from.startswith.assert_called_once_with("s3://")

    @mock.patch("os.path.exists")
    @mock.patch("ratticweb.management.commands.restore.restore")
    def test_converts_FailedBackup_errors_into_CommandError(self, fake_restore, fake_exists):
        default_db = mock.Mock(name="default_db")
        restore_from = mock.Mock(name="restore_from")
        fake_exists.side_effect = lambda p: True
        restore_from.startswith.return_value = False

        error_message = str(uuid.uuid1())
        error = FailedBackup(error_message)
        fake_restore.side_effect = error

        with override_settings(DATABASES={'default': default_db}):
            with self.assertRaisesRegexp(CommandError, error_message):
                # call_command results in the CommandError being caught and propagated as SystemExit
                self.command.handle(restore_from=restore_from)
            fake_exists.assert_called_once_with(restore_from)
            restore_from.startswith.assert_called_once_with("s3://")

    @mock.patch("ratticweb.management.commands.restore.restore")
    def test_uses_restore_location_context_manager(self, fake_restore):
        gpg_home = mock.Mock(name="gpg_home")
        default_db = mock.Mock(name="default_db")
        restore_from = mock.Mock(name="restore_from")
        restore_from_normalized = mock.Mock(name="restore_from_normalized")

        restore_location_cm = mock.MagicMock(name="restore_location_cm")
        restore_location_cm.__enter__.return_value = restore_from_normalized
        restore_location = mock.Mock(return_value=restore_location_cm)

        with override_settings(DATABASES={'default': default_db}, BACKUP_GPG_HOME=gpg_home):
            with mock.patch.object(self.command, "restore_location", restore_location):
                self.command.handle(restore_from=restore_from)

            restore_location.assert_called_once_with(restore_from)
            fake_restore.assert_called_once_with(default_db, restore_from_normalized, gpg_home=gpg_home)

    @mock.patch("ratticweb.management.commands.restore.BackupStorage")
    def test_restore_location_treats_location_as_s3_address_if_starts_with_s3_scheme(self, FakeBackupStorage):
        filename = mock.Mock("filename")

        backup_storage_cm = mock.MagicMock(name="backup_storage_cm")
        backup_storage_cm.__enter__.return_value = filename
        FakeBackupStorage.from_address.return_value = backup_storage_cm

        restore_from = mock.Mock(name="restore_from")
        restore_from.startswith.return_value = True

        with self.command.restore_location(restore_from) as result:
            self.assertIs(result, filename)

    def test_restore_location_returns_location_as_is_if_not_s3_and_exists(self):
        with a_temp_file() as filename:
            with self.command.restore_location(filename) as result:
                self.assertIs(result, filename)

    def test_restore_location_complains_if_no_restore_location_provided(self):
        with self.assertRaisesRegexp(CommandError, "Please specify --restore-from.+"):
            with self.command.restore_location(None):
                assert False, "Should have complained"

    def test_restore_location_complains_if_location_doesnt_exist(self):
        with a_temp_file() as filename:
            os.remove(filename)
            with self.assertRaisesRegexp(CommandError, "Specified backup file \([^\)]+\) doesn't exist"):
                with self.command.restore_location(filename):
                    assert False, "Should have complained"
