from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from ratticweb.management.commands.storage import BackupStorage
from db_backup.errors import FailedBackup
from db_backup.commands import restore

from contextlib import contextmanager
from optparse import make_option


class Command(BaseCommand):
    help = 'Restores an empty database from a backup'

    option_list = BaseCommand.option_list + (
        make_option('--restore-from', help="Location of our backup file"),
    )

    @contextmanager
    def restore_location(self, location):
        """
        Yield the restore location

        If it's a filesystem path, then yield that.

        If it's an s3 path, then download it first
        """

        if location and location.startswith("s3://"):
            with BackupStorage.from_address(location) as filename:
                yield filename
        else:
            if not location:
                raise CommandError("Please specify --restore-from as the location of the backup")

            yield location

    def handle(self, *args, **options):
        """Get necessary options from settings and give to the restore command"""
        gpg_home = getattr(settings, "BACKUP_GPG_HOME", None)
        restore_from = options["restore_from"]

        try:
            with self.restore_location(restore_from) as restore_location:
                restore(settings.DATABASES['default'], restore_location, gpg_home=gpg_home)
        except FailedBackup as error:
            raise CommandError(error)
