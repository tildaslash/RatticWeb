from database_files.storage import DatabaseStorage


class CredAttachmentStorage(DatabaseStorage):
    def url(self, name):
        return 'Not used in RatticDB. If you see this please raise a bug.'
