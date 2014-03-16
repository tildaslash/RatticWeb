from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from ratticweb.management.commands.storage import BackupStorage
from db_backup.errors import FailedBackup
from db_backup.commands import backup

import os


class Command(BaseCommand):
    help = 'Creates an encrypted dump of the database and places it somewhere'

    def validate_options(self, backup_dir, recipients):
        """Make sure our settings make sense"""
        if backup_dir is None:
            raise CommandError("No backup directory has been specified (settings.BACKUP_DIR)")
        if not os.path.exists(backup_dir):
            raise CommandError("Specified backup_dir ({0}) doesn't exist".format(backup_dir))

        if recipients is None:
            raise CommandError("No recipients list has been specified (settings.BACKUP_RECIPIENTS)")
        elif not isinstance(recipients, list) and not isinstance(recipients, tuple) and not isinstance(recipients, basestring):
            raise CommandError("Recipients list needs to be a list of strings or a comma separated string, not {0}".format(type(recipients)))

    def handle(self, *args, **options):
        """Get necessary options from settings and give to the backup command"""
        gpg_home = getattr(settings, "BACKUP_GPG_HOME", None)
        backup_dir = getattr(settings, "BACKUP_DIR", None)
        recipients = getattr(settings, "BACKUP_RECIPIENTS", None)
        self.validate_options(backup_dir, recipients)

        # Make sure the recipients is a list
        if isinstance(recipients, basestring):
            recipients = recipients.split(",")

        try:
            with BackupStorage() as storage:
                destination = backup(settings.DATABASES['default'], recipients, backup_dir, gpg_home=gpg_home)
                storage.send_from(destination, backup_dir)
        except FailedBackup as error:
            raise CommandError(error)
