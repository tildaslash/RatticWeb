from django.conf import settings

from boto.s3.connection import S3Connection
from boto.s3.key import Key
import boto

from db_backup.errors import FailedBackup

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

    It will raise a FailedBackup exception if the S3 bucket doesn't exist
    As part of entry into the context manager
    """
    def __init__(self):
        self.bucket = None
        self.has_storage = False
        self.bucket_location = None

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

    def upload_to_s3(self, source, destination_bucket, key_name):
        """Upload the source to the destination bucket"""
        key = Key(destination_bucket)
        key.key = key_name
        key.set_contents_from_filename(source)
