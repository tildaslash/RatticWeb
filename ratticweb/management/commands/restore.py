from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from db_backup.errors import FailedBackup
from db_backup.commands import restore

from optparse import make_option
import os


class Command(BaseCommand):
    help = 'Restores an empty database from a backup'

    option_list = BaseCommand.option_list + (
        make_option('--restore-from', help="Location of our backup file"),
    )

    def handle(self, *args, **options):
        """Get necessary options from settings and give to the restore command"""
        restore_from = options["restore_from"]

        if not restore_from:
            raise CommandError("Please specify --restore-from as the location of the backup")
        if not os.path.exists(restore_from):
            raise CommandError("Specified backup file ({0}) doesn't exist".format(restore_from))

        try:
            restore(settings.DATABASES['default'], restore_from)
        except FailedBackup as error:
            raise CommandError(error)
