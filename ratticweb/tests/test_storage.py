from django.test.utils import override_settings
from django.test import TestCase

from ratticweb.management.commands.backup import BackupStorage
from db_backup.errors import FailedBackup

from ratticweb.tests.helper import a_temp_file

from moto import mock_s3
import logging
import uuid
import mock
import boto
import os


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

    @mock_s3
    def test_getting_from_s3(self):
        contents = """
        Stuff and things
        blah
        """

        key_name = str(uuid.uuid1())
        bucket_name = str(uuid.uuid1())

        conn = boto.connect_s3()
        conn.create_bucket(bucket_name)

        key = boto.s3.key.Key(conn.get_bucket(bucket_name))
        key.key = key_name
        key.set_contents_from_string(contents)

        with a_temp_file() as location:
            self.storage.get_from_s3(key_name, boto.connect_s3().get_bucket(bucket_name), location)
            with open(location) as fle:
                self.assertEqual(fle.read(), contents)

    @mock_s3
    def test_getting_from_an_address(self):
        contents = """
        Stuff and things
        blah
        """

        bucket_name = str(uuid.uuid1())
        key_name = os.path.join(str(uuid.uuid1()), str(uuid.uuid1()), str(uuid.uuid1()))

        conn = boto.connect_s3()
        conn.create_bucket(bucket_name)

        key = boto.s3.key.Key(conn.get_bucket(bucket_name))
        key.key = key_name
        key.set_contents_from_string(contents)

        with BackupStorage.from_address("s3://{0}/{1}".format(bucket_name, key_name)) as filename:
            with open(filename) as fle:
                self.assertEqual(fle.read(), contents)

        assert not os.path.exists(filename)
