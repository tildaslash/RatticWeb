from django.conf import settings

from boto.s3.connection import S3Connection
from boto.s3.key import Key
import boto

from db_backup.errors import FailedBackup

from contextlib import contextmanager
import urlparse
import tempfile
import logging
import os

log = logging.getLogger("db_backup")


class BackupStorage(object):
    """
    Abstract the task of sending some file to some storage
    This implementation sends to S3

    If settings.BACKUP_S3_BUCKET is None, then it silently assumes
    you don't want anything sent to S3.

    Usage:

        with BackupStorage() as storage:
            source = <some_action>
            storage.send_from(source)

    Or if retreiving:

        with BackupStorage.from_address("s3://my_amazing_bucket/some/key/to/a_file.gpg") as contenst_filename:
            # contents_filename is the path to where the contents were put onto disk
            <some_action with contents_filename>

    It will raise a FailedBackup exception if the S3 bucket doesn't exist
    As part of entry into the context manager
    """

    @classmethod
    @contextmanager
    def from_address(cls, s3_address):
        info = urlparse.urlparse(s3_address)
        if info.scheme != "s3":
            raise FailedBackup("Trying to restore from a non s3 address ({0})".format(s3_address))

        key_name = info.path
        bucket_location = info.netloc.split(":")[0]

        tmp_file = None
        try:
            tmp_file = tempfile.NamedTemporaryFile(delete=False).name
            with BackupStorage(bucket_location) as storage:
                storage.get_from_s3(key_name, storage.bucket, tmp_file)
                yield tmp_file
        finally:
            if tmp_file and os.path.exists(tmp_file):
                os.remove(tmp_file)

    def __init__(self, bucket_location=None):
        self.bucket = None
        self.has_storage = False
        self.bucket_location = bucket_location

    def __enter__(self):
        """Make sure our storage is fine and yield self as the storage helper"""
        try:
            self.validate_destination()
        except (boto.exception.BotoClientError, boto.exception.BotoServerError, boto.exception.NoAuthHandlerFound), error:
            raise FailedBackup("Failed to interact with s3: {0}".format(error))

        return self

    def __exit__(self, typ, val, tb):
        """Nothing to do in exit"""

    def validate_destination(self):
        """Make sure our s3 bucket exists"""
        if not self.bucket_location:
            self.bucket_location = settings.BACKUP_S3_BUCKET

        if self.bucket_location:
            log.info("Connecting to aws")
            conn = S3Connection()

            log.info("Seeing if your bucket exists ({0})".format(self.bucket_location))
            try:
                self.bucket = conn.get_bucket(self.bucket_location)
                self.has_storage = True
            except boto.exception.S3ResponseError, error:
                if error.status == 404:
                    raise FailedBackup("Please first create the s3 bucket where you want your backups to go ({0})".format(self.bucket_location))
                raise

    def send_from(self, source, start):
        """
        Send to our storage from source.
        The s3 key name is retrieved by finding the relative path from start to source
        """
        key_name = os.path.relpath(source, start=start)
        if self.has_storage:
            log.info("Uploading to s3://{0}/{1}".format(self.bucket_location, key_name))
            self.upload_to_s3(source, self.bucket, key_name)

    def move_from(self, source, start):
        """
        Send to our storage from source. Remove when done.
        The s3 key name is retrieved by finding the relative path from start to source
        """
        self.send_from(source, start)
        if self.has_storage:
            log.info('Removing local file {0}'.format(source))
            os.remove(source)

    def upload_to_s3(self, source, destination_bucket, key_name):
        """Upload the source to the destination bucket"""
        key = Key(destination_bucket)
        key.key = key_name
        key.set_contents_from_filename(source)

    def get_from_s3(self, key_name, source_bucket, destination):
        """Get contents from some key into the provided destination"""
        key = source_bucket.get_key(key_name)
        if not key:
            raise FailedBackup("Cannot find key {0} in bucket {1}".format(key_name, source_bucket.name))
        key.get_contents_to_filename(destination)
